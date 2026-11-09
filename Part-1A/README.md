# lcgkit

A toolkit for linear congruential generators (LCGs), the recurrence `x -> (a*x + c) mod m`. It is a Python library, a command-line tool and a stateless HTTP service, and all three give the same answers.

It can generate repeatable sequences, use well-known generators by name, check whether parameters give a full period, jump ahead, draw fair integers and fractions, report on sequence quality, split a sequence into streams, and show how a sequence can be predicted from what has been seen.

## Security

An LCG is not cryptographically secure, and every successful answer says so with `cryptographically_secure: false`. Requests that declare a purpose such as a token, key, password or session are refused. The purpose guard relies on the declared purpose and cannot catch misuse that is not declared.
