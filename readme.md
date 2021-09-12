# Email Finder
This needs a list of homepage URLs. It will try to find emails inside the homepage,
 if not found it will try to find 'contact' page and find emails on that page.
 Otherwise, it will view all the available URLs and load them one by one 
 (its max limit can be set inside [vars.txt](vars.txt) by setting
 `MAX_SUB_URLS`)
 
## Installation & Configuration
It should work on Python 3.8+
You just need to create environment if you want and after that install requirements:
```
> pip install -r requirements.txt
```
After that, update [vars.txt](vars.txt) with your preferences. Details of variables are under:

| VAR NAME     | Description                                                                                                         |
|--------------|---------------------------------------------------------------------------------------------------------------------|
| CHROME_PATH  | open 'chrome://version/' in your chrome and copy the value of 'Executable Path' and apply that for this var         |
| MAX_SUB_URLS | If emails are not found on homepage and contact page, how many URLs on home page should be used to continue search? |
| HEADLESS     | any value if want to hide browser, False if want to see browser.                                                    |
| TIMEOUT      | Page load timeout, if failed it will skip that website.                                                             |
 
 
 ## Run the program
 Just update or overwrite [input.csv](input.csv), with your required brand name and url
 and run the program:

```
> python main.py
``` 