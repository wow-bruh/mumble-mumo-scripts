# Scripts for mumo

### autopm_new

Automatically sends a PM to members online when a new, unregistered user joins.  
**Options:**  
`autopm_new.groups = []`: list of groups to PM  
`autopm_new.message = "New user in the lobby!`: Message to send

### mod_suffixes

Prepends a prefix to some group members.  
**Options:**  
`mod_suffixes.rules = {}`: List of rules to apply, first rules take priority  
`mod_suffixes.rules.group_name = "<name>"`: Name of the group to match   
`mod_suffixes.rules.prefix = "<prefix>"`: Prefix to add for these group members.  

### dnd_spells

Searches a matching DnD spell when called.  
**Usage:** `!spell spell name`  
**Options:**  
`dnd_spells.channels = []`: List of channels to trigger this bot in.

### block_img

Awful attempt at blocking images from being sent. Sadly, that can't be done
