r"""
                                                                   ,---.,---.
,------.                                  ,--.  ,--.               |   ||   |
|  .--. ',--.--. ,---. ,--,--,--. ,---. ,-'  '-.`--' ,---. ,--,--, |  .'|  .'
|  '--' ||  .--'| .-. ||        || .-. |'-.  .-',--.| .-. ||      \|  | |  |
|  | --' |  |   ' '-' '|  |  |  |' '-' '  |  |  |  |' '-' '|  ||  |`--' `--'
`--'     `--'    `---' `--`--`--' `---'   `--'  `--' `---' `--''--'.--. .--.
                                                                   '--' '--'
"""

import discord
from discord.ext import commands
from discord.commands import Option
import json
import re
from sys import stderr
from os import listdir, getenv
import dotenv

# DISCORD_TOKEN is defined in a .env file next to this python script.
# If you want to run Promotion!! locally, create/edit that file and type DISCORD_TOKEN=YourDiscordBotsTokenHere (no quotation marks!)
dotenv.load_dotenv()
bot_token = str(getenv("DISCORD_TOKEN"))

# The intents the bot uses. Default + members for checking role updates.
intents = discord.Intents.default()
intents.members = True

# Create bot object thing and make sure it uses the intents above.
bot = discord.Bot(intents=intents)

# What it does on startup.
@bot.event
async def on_ready():
    print(f"{bot.user} is running!")

# Load mappings from the json files.
# This is to save data if the bot restarts.
def load_mappings():
    try:
        mappings = {}
        for file_name in listdir("assignments/"):
            if file_name.endswith(".json"):
                with open(f"assignments/{file_name}", "r", encoding="utf-8") as f:
                    file = json.load(f)
                    mappings.update(file)
        return mappings
    except Exception as e:
        stderr.write("ERROR LOADING MAPPINGS!\n")
        raise e

# Store mappings in the aforementioned json files, one for every server.
def save_mappings():
    try:
        for server, roles in role_channel_mapping.items():
            with open(f"assignments/{server}.json", "w") as f:
                json.dump({server: roles}, f, indent=4)
    except Exception as e:
        stderr.write(f"Error occurred while saving mappings!\n")
        raise e

# Instantiate mappings dictionary.
# Stores all the servers, roles, channels and messages.
role_channel_mapping = load_mappings()

# Command for assigning an announcement channel when someone gains a role.
@bot.slash_command(
    name="assign",
    description="Assign a role to check for, a channel and a message."
)
# Only admins are allowed to use this command.
@discord.default_permissions(administrator=True)
# Role mandatory, channel and message optional
async def assign_role_and_channel(ctx: discord.ApplicationContext,
                                  role: Option(discord.Role, "The role it should check for.", required=True),
                                  channel: Option(discord.TextChannel, "The channel it should send a message to.", required=False) = None,
                                  message: Option(str, "The message it should send.", required=False) = "{user_mention} got the {role_name} role!! 🎉"
                                  ):
    # If no channel is given, default to the one the command was run in.
    channel = channel or ctx.channel
    # Turn parameter IDs to strings. They're normally integers, this is to avoid converting them every time they are used.
    str_guild_id = str(ctx.guild.id)
    str_role_id = str(role.id)
    str_channel_id = str(channel.id)
    # If the server/role/channel doesn't exist in the json file already, add it.
    if str_guild_id not in role_channel_mapping.keys():
        role_channel_mapping.update({str_guild_id: {}})
    if str_role_id not in role_channel_mapping[str_guild_id].keys():
        role_channel_mapping[str_guild_id].update({str_role_id: {}})
    # If the channel doesn't exist, create a list for messages, otherwise add the message to the list.
    if str_channel_id not in role_channel_mapping[str_guild_id][str_role_id]:
        role_channel_mapping[str_guild_id][str_role_id].update({str_channel_id: [message]})
    else:
        role_channel_mapping[str_guild_id][str_role_id][str_channel_id].append(message)
    # Save the new data in the json file.
    save_mappings()
    # Tell the user the operation succeeded.
    await ctx.respond("Role, channel and message successfully assigned.", ephemeral=True)

# Command for viewing all of the assignments in a server.
@bot.slash_command(
    name="view_assignments",
    description="View all the assignments made in your server."
)
@discord.default_permissions(administrator=True)
async def view_assignments(ctx: discord.ApplicationContext):
    # Initiate an output.
    output = ""
    # Only check the current server.
    for server in role_channel_mapping.keys():
        if server == str(ctx.guild.id):
            # For every role, write the name of it, mention the channel and write the messages under them as bullet points.
            for role in role_channel_mapping[server].keys():
                output += f"## {ctx.guild.get_role(int(role))}\n"
                for channel in role_channel_mapping[server][role].keys():
                    output += f"<#{channel}>\n"
                    for message in role_channel_mapping[server][role][channel]:
                        output += f"- {message}\n"
    # If there are no assignments, tell the user that.
    if not output:
        await ctx.respond("No assignments have been made in this server.", ephemeral=True)
    # Otherwise send complete output.
    else:
        await ctx.respond(output, ephemeral=True)


# Command for removing assignments in a server.
@bot.slash_command(
    name="remove_assignment",
    description="Remove an assignment."
)
@discord.default_permissions(administrator=True)
# Role, channel and message optional.
async def remove_role_channel_assignment(ctx: discord.ApplicationContext,
                                         role: Option(discord.Role, "The role it should delete the assignment of.", required=True) = None,
                                         channel: Option(discord.TextChannel, "The channel where it sends messages.", required=False) = None,
                                         message: Option(str, "The message it sends.", required=False) = None):
    # Instantly give a response so the bot doesn't time out.
    await ctx.respond(f"**WARNING:** Any assignment you remove is **not recoverable.**", ephemeral=True)

    # Turn parameter IDs to strings. They're normally integers, this is to avoid converting them every time they are used.
    str_guild_id = str(ctx.guild.id)
    if role:
        str_role_id = str(role.id)
        str_role_name = str(role)
    if channel:
        str_channel_id = str(channel.id)

    # Check if the parameters exist.
    parameter_existence = (bool(role), bool(channel), bool(message))
    # Helper function for popping a dictionary element after reaction confirmation.
    async def remove_confirmation(confirmation_text: str, output: str, mapping: dict, assignment: str):
        try:
            # Send text, then react with a check and an X emoji.
            confirmation = await ctx.send(confirmation_text)
            await confirmation.add_reaction("✅")
            await confirmation.add_reaction("❌")
            # Check if the person who ran the command reacted, not just anyone.
            def check(reaction, user):
                return user == ctx.author and reaction.message.id == confirmation.id
            # Check to see when the person who ran the command reacted to the message.
            reaction, user = await bot.wait_for("reaction_add", check=check)
            reacted_emoji = str(reaction.emoji)
            if reacted_emoji == "✅":
                # If check mark reaction, delete the assignment.
                mapping.pop(assignment)
                await ctx.send(output)
            if reacted_emoji == "❌":
                await ctx.send("fair enough")
        except Exception as e:
            # Error handling. Log to console, then tell the user.
            stderr.write("ERROR REMOVING ASSIGNMENT\n")
            await ctx.respond("There was an error removing the assignment!", ephemeral=True)
            raise e

    # Do something for when certain parameters exist.
    match parameter_existence:
        # No parameters, remove every assignment.
        case (False, False, False):
            await remove_confirmation("Are you ***absolutely sure*** that you want to delete ***EVERY*** assignment?\n*This cannot be reversed!*",
                                      "Deleted every assignment successfully.",
                                      role_channel_mapping,
                                      str_guild_id)
        # Role parameter, remove every assignment of that role.
        case (True, False, False):
            await remove_confirmation(f"Are you *sure* you want to delete all the assignments made to the {str_role_name} role?",
                                      f"Deleted every assignment to the {str_role_name} role successfully.",
                                      role_channel_mapping[str_guild_id],
                                      str_role_id)
        # Role and channel parameters, remove every assignment of that role in that channel.
        case (True, True, False):
            await remove_confirmation(f"Are you *sure* you want to delete all the assignments from {str_role_name} in {channel.mention}?",
                                      f"Deleted every assignment from {str_role_name} in {channel.mention} successfully.",
                                      role_channel_mapping[str_guild_id][str_role_id],
                                      str_channel_id)
        # All parameters, remove a specific assignment.
        case (True, True, True):
            # Can't use remove_confirmation because I'm removing a value in an array instead of popping a dictionary entry.
            try:
                # If everything is given and the message is in the file, delete it.
                if message in role_channel_mapping[str_guild_id][str_role_id][str_channel_id]:
                    # Send a message and react to it.
                    confirmation = await ctx.send(f"Are you sure you want to remove the following message from {str_role_name} in {channel.mention}?\n{message}")
                    await confirmation.add_reaction("✅")
                    await confirmation.add_reaction("❌")
                    # Check if the person who ran the command reacted, not just anyone.
                    def check(reaction, user):
                        return user == ctx.author and reaction.message.id == confirmation.id
                    # Check to see when the person who ran the command reacted to the message.
                    reaction, user = await bot.wait_for("reaction_add", check=check)
                    reacted_emoji = str(reaction.emoji)
                    # If they reacted with check,
                    if reacted_emoji == "✅":
                        # And it's the only message left in the json file,
                        if role_channel_mapping[str_guild_id][str_role_id][str_channel_id] == [message]:
                            # Remove the entire channel from the file,
                            role_channel_mapping[str_guild_id][str_role_id].pop(str_channel_id)
                        else:
                            # Otherwise remove just the message.
                            role_channel_mapping[str_guild_id][str_role_id][str_channel_id].remove(message)
                        await ctx.send(f'Deleted "{message}" from {str_role_name} in {channel.mention} successfully.')
                    if reacted_emoji == "❌":
                        await ctx.send("fair enough")
                else:
                    # If the message isn't in the file, notify the user.
                    stderr.write("WARNING REMOVING ASSIGNMENT: Message not in assignment.\n")
                    await ctx.send("Message not in assignment.")
            except Exception as e:
                stderr.write("ERROR REMOVING ASSIGNMENT\n")
                await ctx.respond("There was an error removing the assignment!", ephemeral=True)
                raise e
        # Only channel parameter, remove all assignments in that channel.
        case (False, True, False):
            try:
                confirmation = await ctx.send(f"Are you sure you want to remove every assignment in {channel.mention}?")
                await confirmation.add_reaction("✅")
                await confirmation.add_reaction("❌")
                # Check if the person who ran the command reacted, not just anyone.
                def check(reaction, user):
                    return user == ctx.author and reaction.message.id == confirmation.id
                reaction, user = await bot.wait_for("reaction_add", check=check)
                reacted_emoji = str(reaction.emoji)
                # Check to see when the person who ran the command reacted to the message.
                if reacted_emoji == "❌":
                    await ctx.send("fair enough")
                # If they reacted with check,
                if reacted_emoji == "✅":
                    # Initialize check for assignment,
                    channel_has_assignment = False
                    # Create a copy of the server's assignments to prevent changing the iterator size,
                    shadow_mapping = role_channel_mapping[str_guild_id].copy()
                    # And for every role in that copy,
                    for selected_role in shadow_mapping:
                        # If it has an assignment in that channel,
                        if str_channel_id in role_channel_mapping[str_guild_id][selected_role].keys():
                            # Set the check to True,
                            channel_has_assignment = True
                            # And if it's the only channel left in that assignment,
                            if list(role_channel_mapping[str_guild_id][selected_role].keys()) == [str_channel_id]:
                                # Remove the assigned role,
                                role_channel_mapping[str_guild_id].pop(selected_role)
                            else:
                                # Otherwise remove just that assigned channel.
                                role_channel_mapping[str_guild_id][selected_role].pop(str_channel_id)
                    # If the channel isn't present in the server's assignments,
                    if not channel_has_assignment:
                        # Log and notify the user.
                        stderr.write("WARNING REMOVING ASSIGNMENT: Channel has no assignments.\n")
                        await ctx.send("That channel doesn't have any assignments.")
                    else:
                        # Otherwise confirm deletion.
                        await ctx.send(f'Deleted every assignment in {channel.mention} successfully.')
            except Exception as e:
                stderr.write("ERROR REMOVING ASSIGNMENT\n")
                await ctx.respond("There was an error removing the assignment!", ephemeral=True)
                raise e
        # In every other case, log in terminal and tell the user why it didn't work.
        case _:
            stderr.write("WARNING REMOVING ASSIGNMENT: Invalid parameters.\n")
            await ctx.respond("""i can't work with those parameters man

**No parameters** to remove every assignment in the server.
**Role** parameter to remove every assignment to that role.
**Role** and **channel** parameters to remove every assignment of that role in that channel.
**Role**, **channel** and **message** parameters to remove a specific message.
Only **channel** parameter to remove every assignment made in that channel.""", ephemeral=True)
    # Lastly, save everything to the json file.
    save_mappings()

# Command that shows all the tokens that are able to be used with the /assign command and how to use /assign and /remove_assignment.
@bot.slash_command(
    name="help",
    description="How to use the bot."
)
@discord.default_permissions(administrator=True)
# It literally just sends one message. There is no logic behind this. This comment is useless.
async def help(ctx: discord.ApplicationContext):
    await ctx.respond("""
There are only three other commands, `/assign`, `/view_assignments` and `/remove_assignment`.

When using /assign, you can leave out the channel to default to the channel you ran the command in, or the message to default to a fallback message. In the message, you can use the following tokens:
**{user_mention} —** Pings the user that got the role.
**{user_tag} —** Writes the handle of the user that got the role.
**{user_name}** — Writes the display name of the user that got the role.
**{user_id} —** Writes the user ID of the user that got the role.
**{role_mention} —** Pings the received role. **(not recommended)**
**{role_name} —** Writes the name of the received role.
**{role_id} —** Writes the role ID of the received role.

When using /remove_assignment, here are the possible parameter combinations:
**No parameters** to remove every assignment in the server.
**Role** parameter to remove every assignment to that role.
**Role** and **channel** parameters to remove every assignment of that role in that channel.
**Role**, **channel** and **message** parameters to remove a specific message.
Only **channel** parameter to remove every assignment made in that channel.""", ephemeral=True)

# Fun part. What it does when a server member gets a role.
@bot.event
async def on_member_update(before, after):
    # Save all the roles that were added to a user in this list.
    added_roles = [role for role in after.roles if role not in before.roles]
    for role in added_roles:
        # If the role is assigned
        if str(role.id) in role_channel_mapping[str(after.guild.id)].keys():
            # Save all channel IDs and messages to different lists.
            channel_ids = role_channel_mapping[str(after.guild.id)][str(role.id)].keys()
            messages = role_channel_mapping[str(after.guild.id)][str(role.id)].values()
            for channel in channel_ids:
                # Get the actual channel from its ID.
                selected_channel = after.guild.get_channel(int(channel))
                try:
                    # For every message assigned to that channel assigned to that role,
                    for message in role_channel_mapping[str(after.guild.id)][str(role.id)][str(channel)]:
                        # Check for all of these tokens,
                        special_tokens = {"{user_mention}": after.mention,
                                          "{user_tag}": str(after),
                                          "{user_name}": after.display_name,
                                          "{user_id}": after.id,
                                          "{role_mention}": role.mention,
                                          "{role_name}": str(role),
                                          "{role_id}": role.id}
                        for x in special_tokens.keys():
                            # And replace them with the appropriate things,
                            message = re.sub(x, str(special_tokens[x]), message)
                        # Then send the new message in the assigned channel.
                        await selected_channel.send(message)
                except discord.HTTPException as e:
                    print(f"Failed to send message: {e}")
                except Exception as e:
                    print(f"An unexpected error occurred: {e}")
                    raise e

bot.run(bot_token)
