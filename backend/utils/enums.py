# /backend/utils/enums.py

from enum import Enum


class UrlTraverse(str, Enum):
    THIS_ONLY = "this only"
    ALL_DIRECTIONS = "all directions"
    HORIZONTAL = "horizontal"
    DOWN = "down"
    HORIZONTAL_AND_DOWN = "horizontal and down"
