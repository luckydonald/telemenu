# telemenu

### Easily build complex telegram menu logic with almost no code.
<sup><sub><sup><sub><sup>Because I'm writing a lot of code making that possible, lol.</sup></sub></sup></sub></sup>


Currently still a work in progress.

The details of what this library aims for, how it behaves and also some of the needed inner gearing is currently documented in [telemenu/menus_old.py](telemenu/menus_old.py).

```py
menus = TeleMenuMachine(database_driver=SimpleDictDriver(), teleflask_or_tblueprint=bot)

@menus.register
class MainMenu(GotoMenu):
    title = "test"
    description = "Lorem ipsum \n\n We even have access to the data:\n{data!r}"

    def menus(self):
        return [TestMenu, AnotherTestMenu]
    # end def
# end class
```

Have a look at that [example](example/code/example_bot.py), if you like to see a full working example.


# Available variables

### All menus
(e.g. `GotoMenu`)

- `title` (type `str`): The bold headline of the menu.
- `description` (type `str`): The message part with user instructions.


- `_id` (type `str`): This allows you to overwrite the automaticly genereated name of the underlying state. You should probably not change this.

### `GotoMenu`
- `menus` (list containing any `ChangeMenuButton` button subclass (including `GotoButton` and `BackButton`) or simply some other `Menu`s. You can mix those.):
    - This is a list of menus you can jump to.

### `RadioMenu`
- radiobuttons(self) -> (list of `RadioButton` elements): A list of values to choose a single entry from.
