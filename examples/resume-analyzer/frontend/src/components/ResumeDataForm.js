import React, { useState } from 'react';

const ResumeDataForm = () => {
  const [resumeData, setResumeData] = useState({
    name: '',
    email: '',
    phone: '',
    education: [],
    experience: [],
    skills: []
  });

  const handleChange = (e) => {
    setResumeData({ ...resumeData, [e.target.name]: e.target.value });
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    console.log('Resume Data Submitted:', resumeData);
  };

  return (
    <form onSubmit={handleSubmit}>
      <div>
        <label>Name:</label>
        <input type='text' name='name' value={resumeData.name} onChange={handleChange} required />
      </div>
      <div>
        <label>Email:</label>
        <input type='email' name='email' value={resumeData.email} onChange={handleChange} required />
      </div>
      <div>
        <label>Phone:</label>
        <input type='tel' name='phone' value={resumeData.phone} onChange={handleChange} required />
      </div>
      <button type='submit'>Submit</button>
    </form>
  );
};

export default ResumeDataForm;