# Slashee's Cura Posts
## *A selection of questionably useful Cura post processing scripts, for the refined slicer.*
### But how?
To install a script, in Cura, open *Help > Show Configuration Folder*, open the *scripts* folder in there and drop in the .py file.
***
### But why?
Sometimes things bother me. Maybe sometimes things bother you too. If that's the case, why shouldn't we both benefit from my overabundance of free time?
***
## So what's available?
~~[Delete Added Temperature](https://github.com/Slashee-the-Cow/SlasheesCuraPosts/blob/main/DeleteAddedTemperature/DeleteAddedTemperature.zip?raw=true): A temporary workaround to fix a bug in Cura 5.7.2 which can add unwanted temperature instructions at the start of your gcode, depending on your printer's starting gcode.~~  
**[Disable Support Retraction](https://github.com/Slashee-the-Cow/SlasheesCuraPosts/blob/main/DisableSupportRetraction/DisableSupportRetraction.zip?raw=true)**: This one was an audience request. Deletes all retractions while printing support or support interface.  
**[Limit Support Acceleration](https://github.com/Slashee-the-Cow/SlasheesCuraPosts/blob/main/LimitSupportAcceleration/LimitSupportAcceleration.zip?raw=true)**: Allows you to set the acceleration for support sections *and* the travels before and after. I know Cura lets you set the acceleration for support sections individually, but I've been burned by support being pulled and warped as the head moves off at travel speed at the end of the section.  
**[Support Entry/Exit Retract](https://github.com/Slashee-the-Cow/SlasheesCuraPosts/blob/main/SupportEntryExitRetract/SupportEntryExitRetract.zip?raw=true)**: Forces any move from the model to support, or support to model, to retract, regardless of distance.
***
I don't usually get around to testing all of my scripts in new versions of Cura so if something isn't working click the "Issues" link up top and send me a friendly "hey genius, your stuff doesn't work" and I'll have a look at it.
&NewLine;  
&NewLine;  
&NewLine;  
&NewLine;  
*Disclaimers*:
- This is all my own work, except where otherwise noted. I have never contributed to the development of Cura itself.
- No guarantees are offered other than a heartfelt apology if one of these somehow break your printer. But the odds of that happening are extremely low, so please take this note as the joke that it is intended to be.
- You may redistribute the files freely but if you modify it you need to leave an attribution to me in the script.
- I do not, nor have I ever, worked at UltiMaker or any related company (but if there's a job offer, I'm all ears).
