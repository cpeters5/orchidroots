# Contributing to Bluenanta project

We welcome all contributions to OrchidRoots project, whether they are code contributions, documentation improvements, 
bug reports, or feature requests! We appreciate your help in making this project better. 
Here are some guidelines to get you started.
## Table of Contents
* [Code Contribution](#code-contribution)

   * [Getting Started](##getting-started)

   * [How to Contribute](##how-to-contribute)

   * [Development Workflow](##development-workflow)

   * [Code Style Guidelines](##code-style-guidelines)

   * [Pull Request Checklist](##pull-request-checklist)

   * [Encouraging Code Improvement](##encouraging-code-improvement)

   * [Licensing of Contributions](##licensing-of-contribution)

   * [Community Guidelines](##community-guidelines)


* [Documentation Improvement Contribution](#documentation-improvement-contribution)


* [Bug Reports Contribution](#bug-reports-contribution)


* [Feature Requests Contribution](#feature-requests)
---

# Code Contribution

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
5. Create a .env file: The .env file is not included in the repository for security reasons. 
   You will need to create one at the root of the project. Use the following example as a template:
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


6. Database setup: This project uses MariaDB and has not been tested with SQLite. It may not work with SQLite, 
   so ensure you have MariaDB installed and create a local database. Then run migrations.
      ```
      mysql -u root -p
      CREATE DATABASE your-database-name;

      # initial migration for third party
      python manage.py migrate
   
      # Create database schema
      python manage.py makemigrations
      python manage.py migrate
      ```

7. **Import sample data:**  A subset of the data along with associated image files is available 
    under the /data directory.  
   ```
   cd ./data
   tar -xvzf testdata.sql.tar.gz testdata.sql
   mysql -u your-username -p your-database-name < testdata.sql
   ```

8. Expand sample image files and place them in the STATIC_ROOT directory:
   ```
   tar -xvzf ./data/test_imagefiles.tar.gz -C "your path to static root" 
   ```
Now you are ready to start contributing!



## How to Contribute
### Reporting Bugs
Refer to the [Bug Reports](##bug-reports-contribution) section for detailed instructions on reporting bugs.


### Submitting Code Changes
1. Create a new branch for your feature or bug fix:
   ```
   git checkout -b feature/my-feature
   ```
2. Make your changes in the new branch. Ensure your code follows the [Code Style Guidelines](##code-style-guidelines) below.


3. Write unit tests for any new or modified functionality.


4. Commit your changes with a descriptive commit message:
   ```
   git commit -m "Add feature X"
   ```
5. Push your branch to your forked repository:
   ```
   git push origin feature/my-feature
   ```
6. Submit a pull request (PR) from your branch to the main project repository.


### Improving Documentation
Contributions to documentation follow the same workflow as code changes. 
See the [Documentation Improvement Contribution](##document-improvement-contribution) section for details on what can be contributed.


### Interested in Becoming a Maintainer?
If you’re passionate about this project and would like to take a more active role, 
we welcome contributors who are interested in stepping up as maintainers. 
As a maintainer, you’ll help guide the project's direction, review contributions, 
and ensure the project's continued success.

If you're interested, please contact the current maintainers to discuss how you can get involved!



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


## Code Style Guidelines
Please follow the PEP 8 style guide for Python code. We recommend using black for automatic formatting. Here are some specific guidelines:

* Use 4 spaces for indentation.


* Write docstrings for all functions, methods, and classes.


* Use meaningful variable and function names.


* Keep your code DRY (Don’t Repeat Yourself).



## Pull Request Checklist
Before submitting a pull request, ensure the following:

* Code follows PEP 8 and project coding standards.


* Unit tests are added for any new functionality.


* All tests pass locally.


* Changes are documented in the README.md or /docs/ as necessary.



## Encouraging Code Improvement
We welcome contributions to improve the project, especially from developers with more experience or expertise in writing clean, 
efficient, and maintainable code. While the current codebase works, it may not fully adhere to best coding practices. 
We encourage you to bring your skills and knowledge to help make this project even better.

If you spot opportunities to refactor or improve the code structure, we would be grateful for your contributions!



## Licensing of Contributions
By submitting code changes or contributions, you agree that your submissions will be licensed 
under the same MIT License that governs the project. For more details, refer to the [LICENSE.md](LICENSE.md) file in the repository.

If you have any concerns or questions about this, feel free to contact the maintainers.



## Community Guidelines
Be respectful and inclusive to other contributors. We adhere to the Contributor Covenant Code of Conduct to create a positive environment for our project.

---

# Documentation Improvement Contribution
We welcome contributions to improve the documentation, as clear and accurate documentation is essential 
for the project's success. Here are ways you can contribute:

* **Fixing Typos and Grammar:** Review the existing documentation and correct any spelling, grammar, or formatting errors.


* **Clarifying Instructions:** Identify areas where instructions may be unclear or incomplete, and enhance them to make 
  the setup or usage process easier to understand.


* **Adding Missing Information:** If you notice any features or sections not covered in the documentation, 
  feel free to write and submit additional content.


* **Improving Code Comments:** Ensure code is well-documented with clear, concise comments, especially in areas that might be 
  complex or not intuitive.


* **Submitting Example Code:** Add helpful code examples that demonstrate how to use features or modules within the project.

Contributions can be made by submitting pull requests to the documentation files or create a new one.  
If you want to create a new document to expand the project's documentation, please follow these guidelines:

1. Naming Convention: Use clear, descriptive file names that reflect the content (e.g., installation_guide.md, api_reference.md).
   Avoid spaces; use hyphens or underscores instead.


2. Structure: Organize your document with proper headings (use markdown syntax like # Heading 1, ## Heading 2) 
   and include a table of contents if the document is long.


3. Content Clarity: Write in simple, concise language. Break down complex processes into step-by-step instructions and 
   include examples where relevant.


4. Format Consistency: Follow the project's existing formatting style. Use code blocks for any code snippets and 
   maintain uniform bullet points or numbering styles.


5. Location: Place new documents in the documents/ directory. If the document belongs to a specific feature, locate it 
   accordingly within the folder structure.


6. Internal Linking: Ensure that the new document links to other relevant documents when necessary and update the main 
   documentation index (e.g., README.md or documents/index.md) to include a reference to the new file.

When you're ready, submit your new document as a pull request for review.


---
# Bug Reports Contribution
Reporting bugs is a crucial part of improving the project. If you encounter a bug, please follow these guidelines 
when submitting a bug report:

1. **Check Existing Issues:** Before submitting a new bug report, review the Issues page to see if the bug has already 
   been reported or is being addressed.


2. **Create a Detailed Issue:**
  * **Title:** Provide a clear and descriptive title for the issue.


  * **Description:** Explain the bug in detail, including what you expected to happen and what actually happened. 
    If possible, mention how often the bug occurs.


  * **Steps to Reproduce:** Provide step-by-step instructions on how to reproduce the issue. The more precise, the better.


  * **Environment:** Include information about your setup:
    * Operating System
    * Browser (if applicable)
    * Database version (if applicable)
    * Python/Django version or any other relevant software version.
    * Screenshots/Logs: Attach any relevant screenshots, error messages, or logs to help understand the bug.

3. **Severity:** Indicate the severity of the bug (e.g., minor, major, critical) to help prioritize fixing.


4. **Labeling:** If possible, use appropriate labels like bug, help wanted, or good first issue.

Once you've provided all relevant details, submit your bug report via the Issues tab. This will help the maintainers 
and contributors address the issue promptly.
---

# Feature Requests Contribution
We encourage the community to suggest new features that could enhance the project. 
When proposing a new feature, please follow these guidelines to help us understand and evaluate your idea:

1. **Check Existing Requests:** Before submitting a new feature request, browse the Issues page to see if the feature 
   has already been suggested or is under development.


2. **Create a Clear Feature Request:**
   * **Title:** Provide a concise and descriptive title for the feature request.

   * **Description:** Describe the feature in detail, explaining its purpose and how it would benefit the project or its users. Be specific about the problem the feature would solve.
   
   * **Use Case:** Provide one or more scenarios where the feature would be useful. Explain how it would improve workflows, user experience, or project functionality.
   
   * **Proposed Implementation:** If possible, suggest how the feature could be implemented. This can include ideas on what changes need to be made in the codebase or any potential challenges.


3. **Alternatives Considered:** If there are alternative approaches or existing solutions to the problem, mention them and explain why the proposed feature would be preferable.


4. **Labeling:** Use relevant labels like enhancement or feature request to categorize your submission.

Submit your feature request through the Issues tab. The maintainers will review and discuss the request with you and the community to determine if and when the feature can be added to the roadmap.



---