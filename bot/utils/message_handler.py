from discord import Message

thumbs_up_reaction = "\U0001F44D"
thumbs_down_reaction = "\U0001F44E"


async def new_vote_message(message: Message):
    await message.add_reaction(thumbs_up_reaction)
    await message.add_reaction(thumbs_down_reaction)
