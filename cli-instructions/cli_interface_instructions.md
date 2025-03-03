I want you to study the cli_schema.json file and create a python script to:
1. validate the command line arguments against the cli_schema.json description
2. decode the command line arguments to a "configuration" class
3. the configuration class must be used also to read and write the local or global configuration files
4. when the configurtion class is populated by the config files, any command line argument must by added or the same class.
I want you to create also a number (more than 20) of test scenarios that will be used to validate the command line parsing.
The test scenarios must be placed in a json file together with their expected result (success of failure), and you must create a PYTHON script to automated run them and evaluate the results. 

I don't want you to implement any other functionality yet apart of collecting the command line arguments, validating them against the schema definition, populating the configuration class, creating and/or reading the configuration files, and displaying the appropriate help.

