import torch
import torch.nn as nn
import torch.optim as optim

class ResumeData(nn.Module):
    def __init__(self, input_size, hidden_size, output_size):
        super(ResumeData, self).__init__()
        self.fc1 = nn.Linear(input_size, hidden_size)
        self.relu = nn.ReLU()
        self.fc2 = nn.Linear(hidden_size, output_size)

    def forward(self, x):
        out = self.fc1(x)
        out = self.relu(out)
        out = self.fc2(out)
        return out

class JobDescription(nn.Module):
    def __init__(self, input_size, hidden_size, output_size):
        super(JobDescription, self).__init__()
        self.fc1 = nn.Linear(input_size, hidden_size)
        self.relu = nn.ReLU()
        self.fc2 = nn.Linear(hidden_size, output_size)

    def forward(self, x):
        out = self.fc1(x)
        out = self.relu(out)
        out = self.fc2(out)
        return out

# Example usage
if __name__ == '__main__':
    resume_data = ResumeData(input_size=100, hidden_size=50, output_size=1)
    job_description = JobDescription(input_size=100, hidden_size=50, output_size=1)
    print(resume_data)
    print(job_description)