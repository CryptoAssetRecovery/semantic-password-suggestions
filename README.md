# Semantic Similarity Search for Password Canditate Generation
This is a beta version of a semanic search password candidate generator implementing a FAISS Vector DB and embeddings. Passwords are converted to embeddings and stored in the vector db. Each password and its corresponding id (in the vector db) are stored in a PostgresSQL table for reference after search.

## Installation:

### Step 1: Starting a PostgreSQL Database on Localhost and Configuring a User and Password

#### Prerequisites

Ensure that you have PostgreSQL installed on your machine. If not, you can download it from the [official PostgreSQL website](https://www.postgresql.org/download/).

#### Instructions

1. **Start the PostgreSQL service**

   Depending on your operating system, the command to start the PostgreSQL service may vary. Here are some common ones:

   - On Linux (Ubuntu), use the following command:

     ```bash
     sudo service postgresql start
     ```

   - On macOS, if you've installed PostgreSQL via Homebrew, use:

     ```bash
     brew services start postgresql
     ```

   - On Windows, PostgreSQL installs as a service. You can start it from the services console, or use the following command in PowerShell:

     ```powershell
     Start-Service -Name 'postgresql-x64-<version>'
     ```

   Replace `<version>` with your installed PostgreSQL version.

2. **Access the PostgreSQL shell**

   You can access the PostgreSQL shell using the `psql` command. On Linux or macOS, open a terminal and type:

   ```bash
   sudo -u postgres psql
   ```

   On Windows, open the SQL Shell (psql) from the start menu.

3. **Create a new user**

   In the PostgreSQL shell, use the `CREATE USER` command to create a new user. Replace `your_username` with your desired username:

   ```sql
   CREATE USER your_username WITH PASSWORD 'your_password';
   ```

   Replace `your_password` with your desired password.

4. **Grant privileges**

   To grant this user access to create databases, use the following command:

   ```sql
   ALTER USER your_username CREATEDB;
   ```

   Now, your PostgreSQL database is running on localhost, and you have a user configured with a password and the necessary privileges.

Remember to replace `your_username` and `your_password` with your actual username and password. Always ensure your password is strong and secure.

Next, we'll move on to setting up your database...

### Step 2: Configuring a .env File, Starting a Virtual Environment, and Installing Requirements

#### Instructions

1. **Configure a .env file**

   Create a new file in your project root directory and name it `.env`. This file will store your environment variables. Copy and paste the following into your `.env` file:

   ```
   DB_NAME=postgres
   DB_USER=admin
   DB_PASSWORD=examplepassword
   DB_HOST=localhost
   DB_PORT=5432
   ```

   Replace `admin` and `examplepassword` with the username and password you created in the previous step.

2. **Start a virtual environment**

   It's a good practice to create a virtual environment for your Python projects to isolate package installations. If you haven't installed `virtualenv`, you can do so using pip:

   ```bash
   pip install virtualenv
   ```

   Navigate to your project directory and create a new virtual environment. Replace `env` with your preferred environment name:

   ```bash
   virtualenv env
   ```

   To activate the virtual environment:

   - On macOS and Linux:

     ```bash
     source env/bin/activate
     ```

   - On Windows:

     ```powershell
     .\env\Scripts\activate
     ```

3. **Install requirements.txt**

   If you have a `requirements.txt` file in your project, you can install all the necessary dependencies using pip:

   ```bash
   pip install -r requirements.txt
   ```

   If you don't have a `requirements.txt` file, you might need to create one that lists all the Python packages required for your project.

Now, your environment is set up with all the necessary configurations and dependencies. You're ready to start developing your application.

In the next step, we'll discuss how to...

### Step 3: Use the `faiss_updatedb.py` Script to Load the PostgreSQL and Vector Database

#### Disclaimer

This process takes a long time. For crackstations human only list (~70 million passwords) it currently (07/29/2023) takes roughly 8.5 hours to complete. This could be sped up by using the GPUs and possibly using a more efficient embedding model.

#### Instructions

This Python program loads a password list into a PostgreSQL database and creates a FAISS index for efficient similarity search. Here's how to use it:

1. **Prepare your password list**

   The program requires a password list file as input. This should be a text file with one password per line. There are a number of small, prebult lists in the `passwords/` directory. If you'd like to use your own, make sure you have this file ready and know its path.

2. **Run the program**

   You can run the program using the following command:

   ```bash
   python faiss_updatedb.py -w /path/to/your/password_list.txt
   ```

   Replace `/path/to/your/password_list.txt` with the actual path to your password list file.

The program will then load the password list into the PostgreSQL database and create a FAISS index. It will also print progress information and a completion message to the console.

In the next step, we'll discuss how to...

### Step 4: Use the `faiss_search.py` Script to Query the Vector Database

#### Instructions

This python program accepts a password as a command line argument (-p), encodes it using sentance-transformer embeddings and then performs a semantic similarity search in the FAISS Vector DB for k (-k) similar password candidates. The id of the similar embeddings is used to query the PostgresSQL database to find the original password.

1. **Run the program**

   You can run the program using the following command:

   ```bash
   python faiss_search.py -p secretsauce
   ```

   Replace `secretsauce` with the actual password guess.

The program will then load k (if defined, otherwise 15 default) password suggestions into results.json.