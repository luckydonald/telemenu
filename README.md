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

