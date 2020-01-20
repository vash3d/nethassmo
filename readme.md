# NetHassmo
## Automate Welcome Camera presence and monitoring.

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge)](https://github.com/custom-components/hacs)




## Installation

Using [HACS](https://github.com/custom-components/hacs), to install and track updates, is reccomended.

Alternatively, you can download all the files inside the `apps` directory to your local `apps` directory, then add the configuration to enable the `nethassmo` module.

## How it works

This app listen to (user-defined) person entities (and consequently to the associated device tracker) and set Home or Away the corresponding person in Netatmo Welcome camera.
This is especially usefull to avoid manually setting you out when you leave home.

There's is also a "bonus" function to activate/deactivate the camera monitoring.
It's called GuestMode cause it's particularly usefull when you have guests at home to avoid dozens of notification of unknown faces.

## Configuration

To use this app you need an Access Token from Netatmo.  
Browse to https://dev.netatmo.com and login with your account or create one.
Create a new app, give it a name and a description.  
You have to fill `data protection officer name` and `data protection officer email` fields in order to move on (you can simply put your name and email here).  
When you click on SAVE you obtain a `client id` and a `client secret` code. Keep this page open.

In nethassmo folder open nethassmo.cfg with your favorite code editor and fill all the required fields.  
```ini
[ACCESS]
user : youremail@email.com
pswd : yourpassword
client : 4f3ed70814549fb7f98b5t72
secret : D8NzNVhdLMcy0QeTsin3tCcjmu0HGfZme9hKoEXkR
```
key | required | description
-- | -- | --
`user:`| true | the username of your netatmo dev account (email)
`pswd:`| true | the password of your netatmo dev account
`client:`| true | the client id from your app page
`secret:`| true | the client secret from your app page

Save the file.

Next, you can add nethassmo configuration to your apps.yaml file.  
Insert module and class as usual then you have to specify the person sensor the app should listen to. Optionally you can specify an entity (e.g. input_boolean) to control "Guest Mode".

```yaml
nethassmo:
  module: nethassmo
  class: Nethassmo
  persons: ['person.john', 'person.jane', 'person.name_3']
  guest_mode_switch: input_boolean.guestmode
```

key | required | type | default | description
-- | -- | -- | -- | --
`module` | True | string | | The module name of the app.
`class` | True | string | | The name of the Class.
`persons` | True | list | | The person entities to monitor.
`guest_mode_switch` | False | string | | The entity_id you want to use to turn monitoring on/off. Usually an input boolean

Save the file and restart Appdaemon if it not reload the apps.  
The first time Nethassmo is executed it will use the credentials you have previously added for requesting to Netatmo an access token, and your home and persons data.  
All the data will be then added to `nethassmo.cfg`

```ini
[ACCESS]
user : youremail@email.com
pswd : yourpassword
client : 4f3ed70814549fb7f98b5t72
secret : D8NzNVhdLMcy0QeTsin3tCcjmu0HGfZme9hKoEXkR

[TOKEN]
token : 6c7810f49ad10534d29b51e7|ff78959ebeee5fb611a4aba1a37588f5
refresh : 6c7810f49ad10534d29b51e7|fb1d195a5d58cfe6e61287c3a3bfc619

[HOME]
home_id : 6c7810f49ad10534d29b51e7

[PERSONS]
john : not6424b-29c3-4820-79n4-ec9573b68h27
jane : 7u3006cf-c756-4e7c-b44a-e3d7e98637f4
name_3 : xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxx

[SENSORS]
; Edit value (if needed) with the correspondig name from [PERSONS] section
; e.g. ${PERSONS:name}
sensor_john : ${PERSONS:john}
sensor_jane : ${PERSONS:jane}
sensor_name_3 : ${PERSONS:name_3}
```
<u> **IMPORTANT** </u>  
Pay attention at [SENSORS] section.  
The `key` is based on the friendly name of the monitored person.name from Home Assistant (the one you have specified in apps.yaml).  
The corresponding value is a reference to the value of `[PERSONS]` section.
By default Nethassmo app assumes that persons' names in Home Assistant and the ones from Netatmo Welcome camera are the same.  
<u>**If that's not the case you have to manually change the value.**</u>

Taking as an example the configuration above, if in Netatmo Welcome camera the user john had been configured as Johnny instead of John the resulting auto-configuration would had been
```ini
[PERSONS]
johnny : not6424b-29c3-4820-79n4-ec9573b68h27
jane : 7u3006cf-c756-4e7c-b44a-e3d7e98637f4
name_3 : xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxx

[SENSORS]
; Edit value (if needed) with the correspondig name from [PERSONS] section
; e.g. ${PERSONS:name}
sensor_john : ${PERSONS:john}
sensor_jane : ${PERSONS:jane}
sensor_name_3 : ${PERSONS:name_3}
```
So in this case you have to modify `${PERSONS:john}` with `${PERSONS:johnny}`

## Issues/Feature Requests

Please feel free to open any issues or feature requests!

## Note
Theoretically the app should work with multiple cameras but at the moment I can only test it with the one I have.  
If you want you can help me to add a second one ;)
