# Contributing to Bluenanta project

Thank you for considering contributing to [Project Name]! We appreciate your help in making this project better. Here are some guidelines to get you started.

## Table of Contents
* Getting Started
* How to Contribute
* Reporting Bugs
* Submitting Code Changes
* Improving Documentation
* Development Workflow
* Code Style Guidelines
* Pull Request Checklist
* Community Guidelines
---

## Getting Started
1. Fork the repository from GitHub: https://github.com/cpeters5/orchidroots.git
2. Clone your fork locally:
   ```
   git clone https://github.com/cpeters5/orchidroots.git
   cd project-name
   ```
3. Set up a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
4. Install the project dependencies:
   ```
   pip install -r requirements.txt
   ```
5. Create a .env file:
* The .env file is not included in the repository for security reasons. You will need to create one at the root of the project. Use the following example as a template:
   ```
   # .env
   SITE_URL=your site
   SECRET_KEY=your-secret-key
   DBNAME=your-database-name
   PORT=your database port
   DBUSER=your-database-user
   DBPASSWORD=your-database-password
   DBHOST=localhost
   DJANGO_STATIC_ROOT=path to STATIC_ROOT
   DJANGO_MEDIA_ROOT=location=path to MEDIA_ROOT
   ```
* Modify the values as necessary for your local setup and any third party you plan to use.

6. Database setup:
* Note: This project uses MariaDB as the database and has not been tested with SQLite. It may not work with SQLite, 
  so it is recommended to use MariaDB to ensure compatibility.
* Make sure you have MariaDB installed on your system. You can download it from the official MariaDB website.
* Once installed, create a local database for the project
   ```
   mysql -u root -p
   CREATE DATABASE your-database-name;
   ```
  Make sure to update the .env file with the correct database credentials.
* Run migrations for third party apps:
  * Before setting up the project schema, you’ll need to run migrations for third-party apps like allauth and others: 
   ```
   python manage.py migrate
   ```
  
   * This step applies the necessary migrations for external apps, ensuring they work correctly with your local database.
* Create the project schema:
  * After running the initial migration, create the schema for the project by running:
   ```
   python manage.py makemigrations
   python manage.py migrate
   ```
   Note: I personally have a deep fear of running migrations—things tend to go wrong! If any migration issues occur, 
feel free to open an issue or reach out for help.

7. Import sample data:

* A subset of the data along with associated image files is available under the /data directory.
  
* Expand the data file and import it into your local database:
   ```
   # Example import command (adjust as needed for your database setup)
   tar -xvzf ./data/testdata.tar.gz
   cd data
   mysql -u your-username -p your-database-name < testdata.sql
   ```
8. Expand sample image files and place them in the STATIC_ROOT directory:
   ```
   tar -xvzf ./data/test_imagefiles.tar.gz -C "your path to static root" 
   ```
Now you are ready to start contributing!

---

## How to Contribute
### Reporting Bugs
If you find a bug, please create an issue with the following information:

* Steps to reproduce the issue.
* Expected and actual behavior.
* Any relevant error messages or screenshots.

### Submitting Code Changes
1. Create a new branch for your feature or bug fix:
   ```
   git checkout -b feature/my-feature
   ```
2. Make your changes in the new branch. Ensure your code follows the Code Style Guidelines below.
3. Write unit tests for any new or modified functionality.
4. Commit your changes with a descriptive commit message:
   ```
   git commit -m "Add feature X"
   ```
5. Push your branch to your forked repository:
   ```
   git push origin feature/my-feature
   ```
6. Create a pull request (PR) from your branch to the main project repository.

### Improving Documentation
If you want to contribute to the documentation:

* Update or add new information in the /docs/ directory or README.md file.
* Follow the same steps above to submit a pull request.


### Interested in Becoming a Maintainer?
If you’re passionate about this project and would like to take a more active role, 
we welcome contributors who are interested in stepping up as maintainers. 
As a maintainer, you’ll help guide the project's direction, review contributions, 
and ensure the project's continued success.

If you're interested, please contact the current maintainers to discuss how you can get involved!


---

## Development Workflow
1. Manual Testing: While this project does not currently have automated tests, 
   you can manually test your changes using the Django development server:
   ```
   python manage.py runserver
   ```
2. Run test (optional):  If you are familiar with Django’s test framework, 
   feel free to write and run tests using:
   ```
   python manage.py test
   ```
   Contributions that include tests are highly appreciated!
---

## Code Style Guidelines
Please follow the PEP 8 style guide for Python code. We recommend using black for automatic formatting. Here are some specific guidelines:

* Use 4 spaces for indentation.
* Write docstrings for all functions, methods, and classes.
* Use meaningful variable and function names.
* Keep your code DRY (Don’t Repeat Yourself).

---

## Pull Request Checklist
Before submitting a pull request, ensure the following:

* Code follows PEP 8 and project coding standards.
* Unit tests are added for any new functionality.
* All tests pass locally.
* Changes are documented in the README.md or /docs/ as necessary.

---

## Encouraging Code Improvement
We welcome contributions to improve the project, especially from developers with more experience or expertise in writing clean, 
efficient, and maintainable code. While the current codebase works, it may not fully adhere to best coding practices. 
We encourage you to bring your skills and knowledge to help make this project even better.

If you spot opportunities to refactor or improve the code structure, we would be grateful for your contributions!

---

## Licensing of Contributions
By submitting code changes or contributions, you agree that your submissions will be licensed under the same MIT License that governs the project. For more details, refer to the LICENSE.md file in the repository.

If you have any concerns or questions about this, feel free to contact the maintainers.

---

## Community Guidelines
Be respectful and inclusive to other contributors. We adhere to the Contributor Covenant Code of Conduct to create a positive environment for our project.

---


























## Any contributions you make will be under the MIT (LICENSE.md) in the repository
State that when you submit code changes, your submissions are understood to be under the same MIT (LICENSE.md) that covers the project. Feel free to contact the maintainers if that's a concern.

## Report bugs using Github's [issues](https://github.com/cpeters5/bluenanta/issues)
Report a bug by opening a new issue; it's that easy!

**Great Bug Reports** tend to have:
- A quick summary and/or background
- Steps to reproduce
- Be specific!
- What you expected would happen
- What actually happens
- Notes (possibly including why you think this might be happening, or stuff you tried that didn't work)

## Use a Consistent Coding Style
Our project is a Django full-stack application currently using a traditional, method-based approach. 
We are open to evolving our codebase towards a more modern, object-oriented style. 
If you are interested in contributing to this transition, please feel free to submit a pull request to refactor the existing code to an object-oriented paradigm. 
This will help us maintain a clean and efficient code structure moving forward.


## License
By contributing, you agree that your contributions will be licensed under its MIT license'

## References
This document was adapted from the open-source contribution guidelines for [Facebook's Draft](https://github.com/facebook/draft-js).
