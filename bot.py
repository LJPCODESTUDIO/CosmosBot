import discord

client = discord.Client()

emin = 0
ehour = 1
eampm = ' AM'
earth_time = str(ehour) + ':' + str(emin) + eampm
int(ehour)
int(emin)
print(earth_time)
echannel = [796805068447154176, 893715783883059220, 811006764476137532,
            838881658274578473, 796805788311879700, 799897622398631946,
            796805862403604490, 907468129557434368, 914376770608840744,
            855143043840344115, 855268818510020628, 910354953116201030,
            ]

@client.event
async def on_ready():
    print('Bot is ready')

@client.event
async def on_message(message):
    global emin
    global ehour
    global eampm
    global earth_time
    #checks if the bot sent the message
    if message.author == client.user:
        return
    #checks if the author is a bot
    if message.author.bot:
        emin += 1
        print(emin)
        if emin < 10:
            earth_time = str(ehour) + ':0' + str(emin) + eampm
        else:
            earth_time = str(ehour) + ':' + str(emin) + eampm
        int(ehour)
        int(emin)
    #command
    if message.content.startswith('.time'):
        await message.channel.send('the time is: ' + earth_time)

    if discord.CategoryChannel.id == echannel:
        #changes hour
        if emin >= 60:
            emin = 0
            ehour += 1
            if emin < 10:
                earth_time = str(ehour) + ':0' + str(emin) + eampm
            else:
                earth_time = str(ehour) + ':' + str(emin) + eampm
            int(ehour)
            int(emin)
            print(earth_time)
        #stwitches AM PM
        if ehour >= 12:
            ehour = 1
            if eampm == 'AM':
                eampm = 'PM'
            else:
                eampm = 'AM'
            if emin < 10:
                earth_time = str(ehour) + ':0' + str(emin) + eampm
            else:
                earth_time = str(ehour) + ':' + str(emin) + eampm


client.run('NzQwODQ1OTQxMzI5NzU2MjEx.Xyu8jA.SnGX26SORtJj9VBLEusfw7j2DcM')