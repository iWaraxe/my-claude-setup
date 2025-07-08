# Git Commit Slash Command

## Usage
`/git-commit [message]`

## Description
This command helps you create well-structured git commits with descriptive messages and submit them to the repository.

## Instructions
### 1. Stage Your Changes

Before using this command, make sure you have staged the files you want to commit:
```bash
git add .
# or stage specific files
git add path/to/file.txt
```

### 2. Write a Descriptive Commit Message
A good commit message should:
- Use the imperative mood ("Add feature" not "Added feature")
- Start with a verb (add, fix, update, remove, refactor, etc.)
- Be concise but descriptive (50 characters or less for the first line)
- Explain what the change does, not how it does it
- Use present tense

#### Examples of Good Commit Messages:
- `Add user authentication system`
- `Fix dropdown menu positioning issue`
- `Update API endpoint for user profiles`
- `Remove deprecated helper methods`
- `Refactor database connection logic`

#### Examples of Bad Commit Messages:
- `stuff`
- `fixed it`
- `changes`
- `updates and fixes`

### 3. Submit the Commit
The command will:
1. Review your staged changes
2. Create a commit with your message
3. Optionally push to the remote repository (if specified)

### 4. Command Behavior
- If no message is provided, you'll be prompted to write one
- The command will show you what files are being committed
- It will verify the commit was successful
- It can optionally push the changes to the remote repository

### Usage Examples:
```
/git-commit Add new payment processing feature
/git-commit Fix responsive layout on mobile devices
/git-commit Update user dashboard with new metrics
```

## Best Practices
- Commit often with small, focused changes
- Each commit should represent a single logical change
- Test your changes before committing
- Use meaningful commit messages that help other developers understand the change
- Keep commits atomic - if you need to revert, you can revert the entire feature/fix
