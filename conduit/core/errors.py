class DoesNotMatchSchemaError(BaseException):

  def __init__(self, *args: object) -> None:
    super().__init__(*args)


class SchemaNotMentionedError(BaseException):

  def __init__(self, *args: object) -> None:
    super().__init__(*args)


class UnknownFileFormatError(BaseException):

  def __init__(self, *args: object) -> None:
    super().__init__(*args)
