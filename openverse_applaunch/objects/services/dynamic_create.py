import inspect
from typing import Any, Callable, Mapping, TypeAlias, TypedDict


class FuncConfig(TypedDict):
    params: list[str]
    body: str | list[str]


ConfigType: TypeAlias = list[FuncConfig]
ListFuncType: TypeAlias = list[Callable[..., Any]]
FuncType: TypeAlias = Callable[..., Any]


arguments: dict[str, Any] = {
    "a": 1,
    "b": 2,
    "text1": 'Привет Мир!',
    "text2": "!",
    "separator": " ",
    "base": 1,
    "exponent": 10,
}


# this needs for dynamic create func with config
def create_dynamic_func(func_configurations: ConfigType) -> ListFuncType:
    function: ListFuncType = []
    for config in func_configurations:
        params_func = config['params']
        raw_body_code = config['body']

        if isinstance(raw_body_code, list):
            body_code = "\n".join(raw_body_code)
        else:
            body_code = raw_body_code

        params_str = ', '.join(params_func)
        func_code = f'def dynamic_func({params_str}):\n'
        for line in body_code.split("\n"):
            func_code += f'    {line}\n'

        local_vars = {}
        global_vars = globals().copy()
        exec(func_code, global_vars, local_vars)
        function.append(local_vars['dynamic_func'])
    return function


def execute_dynamic_func(function: FuncType,
                         available_args: Mapping[str, Any]) -> Any:
    pos_args: list[Any] = []
    kw_args: dict[str, Any] = {}
    var_kwargs: dict[str, Any] = {}

    sig = inspect.signature(function)
    
    # Отдельно обрабатываем VAR_KEYWORD параметры
    for name, value in available_args.items():
        if name not in sig.parameters:
            var_kwargs[name] = value
    
    # Обработка параметров функции
    for name, sig_param in sig.parameters.items():
        if sig_param.kind == inspect.Parameter.VAR_POSITIONAL:
            # Для *args пропускаем, так как мы не знаем, какие параметры 
            # должны пойти в *args
            continue
        if sig_param.kind == inspect.Parameter.VAR_KEYWORD:
            # Для **kwargs пропускаем, мы уже заполнили var_kwargs выше
            continue

        if name in available_args:
            if sig_param.kind == inspect.Parameter.POSITIONAL_ONLY:
                pos_args.append(available_args.get(name))
            elif sig_param.kind in (inspect.Parameter.POSITIONAL_OR_KEYWORD,
                                    inspect.Parameter.KEYWORD_ONLY):
                kw_args[name] = available_args.get(name)

    try:
        print(f"\nФункция: {function.__name__}")
        print(f"Сигнатура: {sig}")
        print(f"Вызываем с позиционными аргументами: {pos_args}")
        print(f"Вызываем с именованными аргументами: {kw_args}")
        print(f"Дополнительные аргументы для **kwargs: {var_kwargs}")

        # Объединяем обычные kwargs с дополнительными kwargs
        combined_kwargs = {**kw_args, **var_kwargs}
        result_func = function(*pos_args, **combined_kwargs)

        print(f"Результат: {result_func}")
        return result_func
    except Exception as e:
        print(f"Ошибка при вызове функции: {e}")
        return None             


configurations: ConfigType = [
    {
        'params': ['a', 'b'],
        'body': "return a + b"
    },
    {
        'params': ['text1', 'text2', 'separator'],
        'body': "return text1 + separator + text2"
    },
    {
        'params': ['base', 'exponent'],
        'body': "return base * exponent"
    },
    {
        'params': ['*args', '**kwargs'],
        'body': """result = sum(args)
for key, value in kwargs.items():
    result += value
return result"""
    }
]

if __name__ == "__main__":
    my_functions = create_dynamic_func(func_configurations=configurations)
    for func in my_functions:
        execute_dynamic_func(func, available_args=arguments)
