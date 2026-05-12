# -*- coding: utf-8 -*-
#
# Copyright (c) Broadcom. All Rights Reserved.
# The term “Broadcom” refers solely to the Broadcom Inc. corporate affiliate that
# distributes this software.
#
# You are hereby granted a non-exclusive, worldwide, royalty-free license under
# Broadcom’s copyrights to use, copy, modify, and distribute this software in source
# code or binary form for use in connection with Broadcom products.
#
# This copyright notice shall be included in all copies or substantial portions of the
# software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
# PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF
# CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE
# OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

from typing import List, Dict

"""
This module contains the definition of the `Result` class.

Attributes:
    status_code (int): The status code of the result.
    message (str): The message associated with the result.
    data (List[Dict]): The data associated with the result.

Methods:
    __init__(self, status_code: int, message: str = '', data: List[Dict] = None): Initializes a new instance of the
        `Result` class.
    add_data(self, new_data: Dict): Helper method ensures that only dictionaries are allowed to be added
"""


class Result:
    def __init__(self, status_code: int, message: str = "", data: List[Dict] = None):
        self.status_code = status_code
        self.message = message
        self.data = data if isinstance(data, list) else []

    def add_data(self, new_data: Dict):
        if isinstance(new_data, dict):
            self.data.append(new_data)
        else:
            raise ValueError("Data must be a dictionary")
