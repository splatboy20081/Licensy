from typing import Iterable, Iterator, Any, Set, Callable, Union

import discord


def cycle(iterable: Iterable[Any]) -> Iterator[Any]:
    """
    Similar to itertools.cycle but doesn't make unnecessary copies and just works directly with iterator.

    Usage
    -----
    cycle([1, 2, 3]) --> 1 2 3 1 2 3 1 2 3 ...

    Parameters
    ----------
    iterable: Any
        Any object that has __iter__ method.

    Returns
    -------
    Iterator: Any
        Iterator that cycles over param iterable, meaning if it reaches end it will start over.
    """
    while iterable:
        for element in iterable:
            yield element


class HashableActivity(discord.Activity):
    """Represents hashable discord.Activity so it can be added to sets."""
    def __key(self):
        return self.name, self.type

    def __hash__(self):
        return hash(self.__key())


class DynamicActivity(HashableActivity):
    """
    Activity that is hashable and implements additional attribute that stores callable used for
    generating activity name.
    """
    def __init__(self, name_callable: Callable[[], str], **kwargs):
        """
        Parameters
        ----------
        name_callable: Callable[[], str]
            Callable (eg. reference to function) that, when called, should return string representing freshly
            generated activity name. Examples:
            DynamicActivity(lambda: "Some name")
            DynamicActivity(some_function)
        kwargs
            Any additional options to be passed to discord.Activity.
        """
        super().__init__(**kwargs)
        self._name_callable = name_callable

    @property
    def name_callable(self) -> Callable[[], str]:
        """
        Returns callable that, when called, will return string representing activity name.

        Returns
        -------
        activity name: str
            Represents newly generated activity name.
        """
        return self._name_callable

    def update_name(self) -> None:
        """
        Updates this activity name to the return value of name_callable()
        """
        self.name = self.name_callable()


class ActivityCycle:
    """
    Inexhaustible iterator that cycles infinitely trough all added activities.

    Activity names are only constructed (and updated) when the iterator is actually called,
    so you won't get any stale data.

    Cycle cannot be reset, there will always be one iterator (eg. for activity in activity_cycle will not reset cycle).

    You can add new activities at any time but you can't remove them.
    Added activities have to be instance of DynamicActivity but if they're not then they can be
    instance of discord.BaseActivity

    Activities will be stored in set meaning:
     1. There will be no duplicates.
     2. Activities will not come out in the same order as you've put them in but they will be
        ordered when you get them, visual example:
           in -> 1, 2, 3
        All these could then be valid:
           out -> 1, 2, 3, 1, 2, 3, 1, 2, 3, 1 ...
           out -> 2, 3, 1, 2, 3, 1, 2, 3, 1, 2...
           out -> 3, 1, 2, 3, 1, 2, 3, 1, 2, 3 ...

    Usage
    ----------
    bot = # your Discord bot

    example_cycle = ActivityCycle()

    example_cycle.add(
        DynamicActivity(
            type=discord.ActivityType.watching,
            name_callable=lambda: "{} guilds".format(len(bot.guilds))
        )
    )

    def stream_name_helper() -> str:
        example_names = ("Subscribe!", "Follow!", "Join!")
        return random.choice(example_names)

    example_cycle.add(
        DynamicActivity(
            type=discord.ActivityType.streaming,
            name_callable=stream_name_helper,
            url="https://www.twitch.tv/"
        )
    )

    example_cycle.add(
        discord.Game(
            name="Coding but not dynamic"
        )
    )

    # Then either iterate over it
    for activity in example_cycle:
        await bot.change_presence(activity)
        await asyncio.sleep(300)

    # Or manually call next
    @tasks.loop(minutes=5.0)
    async def activity_loop():
        await bot.change_presence(activity.next())
    """
    def __init__(self):
        self._activities: Set[DynamicActivity] = set()
        self._cycle_activities: Iterator[DynamicActivity] = cycle(self._activities)

    def __iter__(self) -> Iterator[Union[DynamicActivity, discord.BaseActivity]]:
        """
        Inexhaustible iterator (cycles trough iterable).
        """
        return self

    def __next__(self) -> Union[DynamicActivity, discord.BaseActivity]:
        """
        Reconstructs the activity name (to avoid stale data, example old guild count) and returns said activity.
        If activity is not DynamicActivity then it skips the name reconstruction part and just returns the activity.

        Returns
        -------
        activity: Union[DynamicActivity, discord.BaseActivity]
            Stored discord activity (with refreshed message if stored activity was DynamicActivity).
        """
        activity = self._cycle_activities.__next__()
        if isinstance(activity, DynamicActivity):
            activity.update_name()

        return activity

    def next(self) -> Union[DynamicActivity, discord.BaseActivity]:
        """
        Alias for self.__next__()
        """
        return self.__next__()

    def add(self, activity: Union[DynamicActivity, discord.BaseActivity]) -> None:
        """
        Add activity to this iterable.

        Parameters
        ----------
        activity: : Union[DynamicActivity, discord.BaseActivity]
            Activity to add to this iterable.
        """
        self._activities.add(activity)
