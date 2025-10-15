// JavaScript to handle showing and hiding forms and auth buttons
function toggleRequiredFields(userType) {
  const studentFields = document.getElementById('student-fields');
  const officerFields = document.getElementById('officer-fields');

  // Student fields
  Array.from(studentFields.querySelectorAll('input')).forEach((input) => {
    if (userType === 'student') {
      input.setAttribute('required', 'required');
    } else {
      input.removeAttribute('required');
    }
  });

  // Officer fields
  Array.from(officerFields.querySelectorAll('input')).forEach((input) => {
    if (userType === 'officer') {
      input.setAttribute('required', 'required');
    } else {
      input.removeAttribute('required');
    }
  });
}

function showLogin(userType) {
  // Hide auth buttons
  document.getElementById('auth').style.display = 'none';

  // Show login, hide register
  document.getElementById('login-form').style.display = 'block';
  document.getElementById('register-form').style.display = 'none';

  // Update login title
  document.getElementById('login-title').textContent =
    userType.charAt(0).toUpperCase() + userType.slice(1) + ' Login';

  // Reset register-specific fields visibility
  document.getElementById('student-fields').style.display = 'none';
  document.getElementById('officer-fields').style.display = 'none';

  toggleRequiredFields(null);
}

function showRegister(userType) {
  // Hide auth buttons
  document.getElementById('auth').style.display = 'none';

  // Show register, hide login
  document.getElementById('login-form').style.display = 'none';
  document.getElementById('register-form').style.display = 'block';

  // Update register title
  document.getElementById('register-title').textContent =
    userType.charAt(0).toUpperCase() + userType.slice(1) + ' Register';

  // Toggle fields based on user type
  if (userType === 'student') {
    document.getElementById('student-fields').style.display = 'block';
    document.getElementById('officer-fields').style.display = 'none';
  } else if (userType === 'officer') {
    document.getElementById('student-fields').style.display = 'none';
    document.getElementById('officer-fields').style.display = 'block';
  }

   toggleRequiredFields(userType);
}

function showAuth() {
  // Show only auth buttons
  document.getElementById('auth').style.display = 'flex';
  document.getElementById('login-form').style.display = 'none';
  document.getElementById('register-form').style.display = 'none';

  // Reset register-specific fields
  document.getElementById('student-fields').style.display = 'none';
  document.getElementById('officer-fields').style.display = 'none';
}

// ==========================
// Form submission handlers
// ==========================
document.getElementById('register').addEventListener('submit', async (e) => {
  e.preventDefault();

  // Handle required fields dynamically
  const studentFields = document.getElementById('student-fields');
  const officerFields = document.getElementById('officer-fields');

  Array.from(studentFields.querySelectorAll('input')).forEach((input) => {
    if (studentFields.style.display === 'none') {
      input.removeAttribute('required');
    } else {
      input.setAttribute('required', 'required');
    }
  });

  Array.from(officerFields.querySelectorAll('input')).forEach((input) => {
    if (officerFields.style.display === 'none') {
      input.removeAttribute('required');
    } else {
      input.setAttribute('required', 'required');
    }
  });

  const formData = new FormData(e.target);
  const data = Object.fromEntries(formData);
  data.skills = data.skills ? data.skills.split(',').map((s) => s.trim()) : [];

  const userType = document
    .getElementById('register-title')
    .textContent.toLowerCase()
    .includes('student')
    ? 'student'
    : 'officer';

  const endpoint = `/api/${userType}/register`;

  try {
    const response = await fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    const result = await response.json();
    if (response.ok) {
      alert(result.message);
      showLogin(userType); // Redirect to login after register
    } else {
      alert(result.error);
    }
  } catch (error) {
    alert('Registration failed');
  }
});

document.getElementById('login').addEventListener('submit', async (e) => {
  e.preventDefault();
  const formData = new FormData(e.target);
  const data = Object.fromEntries(formData);

  const userType = document
    .getElementById('login-title')
    .textContent.toLowerCase()
    .includes('student')
    ? 'student'
    : 'officer';

  const endpoint = `/api/${userType}/login`;

  try {
    const response = await fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    const result = await response.json();
    if (response.ok) {
      localStorage.setItem('token', result.token);
      localStorage.setItem('role', userType);
      // Redirect to dashboard
      window.location.href = `${userType}/dashboard.html`;
    } else {
      alert(result.error);
    }
  } catch (error) {
    alert('Login failed');
  }
});

// ==========================
// Initialize on page load
// ==========================
document.addEventListener('DOMContentLoaded', () => {
  showAuth();
});
