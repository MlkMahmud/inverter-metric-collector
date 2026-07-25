from random import randbytes, randint
from typing import List, Union
from unittest.mock import MagicMock

import pytest

from utils import retry


class TestRetry:
    def test_calls_passed_in_fn_at_least_once(self):
        fn = MagicMock()
        retry(fn)

        fn.assert_called()

    def test_propagates_return_value_of_passed_in_function(self, mock_time: MagicMock):
        return_value = randbytes(8)
        fn = MagicMock(return_value=return_value)

        result = retry(fn)

        mock_time.sleep.assert_not_called()
        assert result == return_value

    def test_does_not_propagate_exceptions_before_a_given_number_of_retries(
        self, mock_time: MagicMock
    ):
        return_value = 3
        num_of_retries = randint(1, 3)
        side_effect: List[Union[int, RuntimeError]] = [
            RuntimeError("internal error") for _ in range(num_of_retries)
        ]
        side_effect.append(return_value)

        fn = MagicMock(side_effect=side_effect)

        result = retry(fn, retries=num_of_retries)

        assert fn.call_count == num_of_retries + 1
        assert mock_time.sleep.call_count == num_of_retries
        assert result == return_value

    def test_propagates_exceptions_after_a_given_number_of_reties(
        self, mock_time: MagicMock
    ):
        exc_message = str(randbytes(10))

        num_of_retries = randint(1, 3)
        side_effect: List[RuntimeError] = [
            RuntimeError(exc_message) for _ in range(num_of_retries + 1)
        ]

        fn = MagicMock(side_effect=side_effect)

        with pytest.raises(RuntimeError) as exc_info:
            retry(fn, retries=num_of_retries)

        assert fn.call_count == num_of_retries + 1
        assert mock_time.sleep.call_count == num_of_retries
        assert str(exc_info.value) == exc_message
