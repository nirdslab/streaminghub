# Code Refactoring Example

Here's an example of converting an existing data streaming code to use with StreamingHub.

The key idea is as follows:

* Separate out code related to data loading, and make it reusable by adding metadata.
* Separate out code related to calling the algorithm from the algorithm itself.
* Wrap data loading, algorithm calling, and algorithm into their own class.
