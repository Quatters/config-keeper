from config_keeper import console


def print_project_saved(project: str):
    console.print(f'Project "{project}" saved.')


def print_warning(msg: str):
    console.print('Warning:', end=' ', style='yellow')
    console.print(msg)


def print_error(msg: str):
    console.print('Error:', end=' ', style='red')
    console.print(msg)


def print_critical(msg: str):
    console.print('Critical:', end=' ', style='violet')
    console.print(msg)


def print_tip(msg: str):
    console.print('Tip:', end=' ', style='yellow')
    console.print(msg)
