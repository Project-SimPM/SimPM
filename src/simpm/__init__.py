"""SimPM is a Simulation Tool in Project Management (https://github.com/Project-SimPM/SimPM). Current subpackage includes des (discrete event simulation), and dists(probability distributions) modules.
"""
from simpm.des import *
from simpm.dist import *
from simpm.log_cfg import log_config, logger
from simpm.runner import run

__version__ = "2.1.1"
