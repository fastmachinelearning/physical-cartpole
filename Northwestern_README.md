# Instructions For Cloning On Kona

## Step 1: Environment Setup

**Important**: These Steps assume that you are using the Kona lab server, or some sort of SSH

### Check for Existing SSH Key
Open a terminal on Kona and run this command:

```bash
ls -al ~/.ssh
```

If you see files like id_rsa and id_rsa.pub, an SSH key already exists. If not, proceed to the next step

### Generate an SSH Key (if needed)
Run the following to create an SSH key: 

```bash
ssh-keygen -t rsa -b 4096 -C "your_email@example.com"
```

Press Enter to save the key in the default location (~/.ssh/id_rsa) and set a passphrase if desired 

### Add that SSH Key to your GitHub.
Copy the SSH key to your clipboard: 
```bash
cat ~/.ssh/id_rsa.pub
```

Then, log in to GitHub, go to Settings > SSH and GPG keys, and paste the key

### Clone the Github repository
To clone the repository along with its submodules, use the SSH URL:

```bash
git clone --recurse-submodules git@github.com:fastmachinelearning/physical-cartpole.git && cd physical-cartpole
```

**Note**: Using SSH is required because the submodules are cloned using SSH. If you don't have SSH configured, the submodule cloning will fail