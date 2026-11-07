import pytest
from scripts.generate_samples import generate_samples

@pytest.mark.parametrize('num_samples', [3])
def test_generate_samples(num_samples):
    samples = generate_samples(num_samples)
    assert len(samples) == num_samples
    assert all(isinstance(sample, str) for sample in samples)