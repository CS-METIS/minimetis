import typing as type

JSONType = type.Union[str, int, float, bool, None, type.Dict[str, type.Any], type.List[type.Any]]
NodeType = type.Tuple[str, type.Dict[str, str]]
