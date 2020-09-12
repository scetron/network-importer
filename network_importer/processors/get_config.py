import os
import pdb
import logging
from pathlib import Path

from typing import Dict
import hashlib

from nornir.core import Nornir
from nornir.core.inventory import Host
from nornir.core.task import AggregatedResult, MultiResult, Result, Task

import network_importer.config as config
from network_importer.processors import BaseProcessor

logger = logging.getLogger("network-importer")


class GetConfig(BaseProcessor):

    task_name = "get_config"
    config_extension = "txt"

    def __init__(self) -> None:
        self.current_md5 = dict()
        self.previous_md5 = dict()
        self.config_filename = dict()
        self.config_dir = None
        self.existing_config_hostnames = None

    def task_started(self, task: Task) -> None:
        """Before Update all the config file, 
            - ensure that the configs directory exist
            - check what config files are already present

        Args:
            task (Task): Nornir Task
        """

        if not os.path.isdir(config.main["configs_directory"]):
            os.mkdir(config.main["configs_directory"])
            logger.debug(f"Configs directory created at {config.main['configs_directory']}")

        self.config_dir = config.main["configs_directory"] + "/configs"

        if not os.path.isdir(self.config_dir):
            os.mkdir(self.config_dir)
            logger.debug(f"Configs directory created at {self.config_dir}")

        # Save the hostnames associated with all existing configurations before we start the update process
        self.existing_config_hostnames = [
            f.split(f".{self.config_extension}")[0] for f in os.listdir(self.config_dir) if f.endswith(".txt")
        ]

    def task_completed(self, task: Task, result: AggregatedResult) -> None:
        """At the end, remove all configs files that have not been updated 
        to ensure that we are loading just the right config files in Batfish
        """

        if len(self.existing_config_hostnames) > 0:
            logger.info(f"Will delete {len(self.existing_config_hostnames)} config(s) that have not been updated")

            for f in self.existing_config_hostnames:
                os.remove(os.path.join(self.config_dir, f"{f}.{self.config_extension}"))

    def subtask_instance_started(self, task: Task, host: Host) -> None:
        """Before getting the new configuration, check if a configuration already exist and calculate it's md5

        Args:
            task (Task): Nornir Task
            host (Host): Nornir Host
        """
        if task.name != self.task_name:
            return

        self.config_filename[host.name] = f"{self.config_dir}/{task.host.name}.{self.config_extension}"

        if os.path.exists(self.config_filename[host.name]):
            current_config = Path(self.config_filename[host.name]).read_text()
            self.previous_md5[host.name] = hashlib.md5(current_config.encode("utf-8")).hexdigest()

    def subtask_instance_completed(self, task: Task, host: Host, result: MultiResult) -> None:

        if task.name != self.task_name:
            return

        if result[0].failed:
            logger.warning(f"{task.host.name} | Something went wrong while trying to update the configuration ")
            host.data["status"] = "fail-other"
            return

        config = result[0].result.get("config", None)

        if not config:
            logger.warning(f"{task.host.name} | No configuration return ")
            host.data["status"] = "fail-other"
            return

        if host.name in self.existing_config_hostnames:
            self.existing_config_hostnames.remove(host.name)

        # Save configuration to to file and verify the new MD5
        with open(self.config_filename[host.name], "w") as config_:
            config_.write(config)

        self.current_md5[host.name] = hashlib.md5(config.encode("utf-8")).hexdigest()
        changed = False

        if host.name in self.previous_md5 and self.previous_md5[host.name] == self.current_md5[host.name]:
            logger.debug(f"{task.host.name} | Latest config file already present ... ")
        else:
            logger.info(f"{task.host.name} | Configuration file updated ")
            changed = True
