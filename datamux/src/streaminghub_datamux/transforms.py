import streaminghub_datamux as datamux


class ExpressionMapper:

    def __init__(self, mapping: dict[str, str]) -> None:
        self.mapping = mapping

    def __call__(self, msg: dict):
        if msg == datamux.END_OF_STREAM:
            return datamux.END_OF_STREAM
        index, value = msg["index"], msg["value"]
        target = {}
        for k, expr in self.mapping.items():
            target[k] = eval(expr, {**index, **value})
        return target
