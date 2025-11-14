// Officer Dashboard specific JavaScript

const API_BASE = '';
const token = localStorage.getItem('token');

document.addEventListener('DOMContentLoaded', () => {
  if (!token) {
    window.location.href = '/';
    return;
  }
  loadActivePostings();
  loadApplicationPipeline();
  loadRecentApplications();
  loadOfficerReports();
  loadOfficerNotifications();
});

// Load Officer Profile Info - Removed as per user request

// Load Active Postings
async function loadActivePostings() {
  try {
    const res = await fetch(`${API_BASE}/api/officer/postings`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    if (res.ok) {
      const postings = await res.json();
      const activePostings = document.getElementById('active-postings');
      if (postings.length > 0) {
        activePostings.innerHTML = postings.slice(0, 3).map(posting => `
          <div class="posting-card">
            <h3>${posting.title}</h3>
            <p><strong>Description:</strong> ${posting.description || 'N/A'}</p>
            <p><strong>Eligibility:</strong> Branch: ${posting.branch_eligibility || 'N/A'}, CGPA: ${posting.min_cgpa || 'N/A'}</p>
            <p><strong>Package:</strong> ${posting.package_stipend || 'N/A'}</p>
            <button onclick="editPosting(${posting.job_id})">Edit</button>
          </div>
        `).join('');
      } else {
        activePostings.innerHTML = '<p>No active postings.</p>';
      }
    } else {
      document.getElementById('active-postings').innerHTML = '<p>Failed to load postings.</p>';
    }
  } catch (error) {
    console.error('Error loading postings:', error);
    document.getElementById('active-postings').innerHTML = '<p>Error loading postings.</p>';
  }
}

// Load Registered Students
async function loadRecentApplications() {
  try {
    const res = await fetch(`${API_BASE}/api/student/list`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    if (res.ok) {
      const students = await res.json();
      const studentsTable = document.getElementById('recent-applications');
      if (students.length > 0) {
        studentsTable.innerHTML = `
          <input type="text" id="student-search" placeholder="Search by roll number, branch, or skill..." onkeyup="filterStudents()">
          <table id="students-table">
            <thead>
              <tr>
                <th>Student ID</th>
                <th>University Roll Number</th>
                <th>Name</th>
                <th>Email</th>
                <th>Branch</th>
                <th>CGPA</th>
                <th>Skills</th>
                <th>Resume</th>
              </tr>
            </thead>
            <tbody>
              ${students.map(student => `
                <tr>
                  <td>${student.student_id}</td>
                  <td>${student.university_roll}</td>
                  <td>${student.name}</td>
                  <td>${student.email}</td>
                  <td>${student.branch}</td>
                  <td>${student.cgpa}</td>
                  <td>${student.skills ? student.skills.join(', ') : 'N/A'}</td>
                  <td>${student.resume_path ? `<a href="/uploads/${student.resume_path.split('/').pop()}" target="_blank">View</a>` : 'N/A'}</td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        `;
      } else {
        studentsTable.innerHTML = '<p>No registered students.</p>';
      }
    } else {
      document.getElementById('recent-applications').innerHTML = '<p>Failed to load students.</p>';
    }
  } catch (error) {
    console.error('Error loading students:', error);
    document.getElementById('recent-applications').innerHTML = '<p>Error loading students.</p>';
  }
}

// Filter students by roll number, branch, or skill
function filterStudents() {
  const input = document.getElementById('student-search');
  const filter = input.value.toLowerCase();
  const table = document.getElementById('students-table');
  const tr = table.getElementsByTagName('tr');

  for (let i = 1; i < tr.length; i++) {
    const tdRollNo = tr[i].getElementsByTagName('td')[0]; // Student ID
    const tdUniRollNo = tr[i].getElementsByTagName('td')[1]; // University Roll Number
    const tdBranch = tr[i].getElementsByTagName('td')[4];
    const tdSkills = tr[i].getElementsByTagName('td')[6];
    if (tdRollNo || tdUniRollNo || tdBranch || tdSkills) {
      const txtValueRollNo = tdRollNo.textContent || tdRollNo.innerText;
      const txtValueUniRollNo = tdUniRollNo.textContent || tdUniRollNo.innerText;
      const txtValueBranch = tdBranch.textContent || tdBranch.innerText;
      const txtValueSkills = tdSkills.textContent || tdSkills.innerText;
      if (txtValueRollNo.toLowerCase().indexOf(filter) > -1 ||
          txtValueUniRollNo.toLowerCase().indexOf(filter) > -1 ||
          txtValueBranch.toLowerCase().indexOf(filter) > -1 ||
          txtValueSkills.toLowerCase().indexOf(filter) > -1) {
        tr[i].style.display = '';
      } else {
        tr[i].style.display = 'none';
      }
    }
  }
}

// Load Officer Reports
async function loadOfficerReports() {
  try {
    // Fetch postings and applications to calculate reports
    const postingsRes = await fetch(`${API_BASE}/api/officer/postings`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    const appsRes = await fetch(`${API_BASE}/api/officer/applications`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    if (postingsRes.ok && appsRes.ok) {
      const postings = await postingsRes.json();
      const apps = await appsRes.json();
      const totalPostings = postings.length;
      const totalApps = apps.length;
      const selected = apps.filter(app => app.status === 'Selected').length;
      // Assuming package is not in applications, set to 0 for now
      const avgPackage = 0;

      document.getElementById('total-postings').textContent = totalPostings;
      document.getElementById('total-apps').textContent = totalApps;
      document.getElementById('selected-students').textContent = selected;
      document.getElementById('avg-package').textContent = avgPackage;
    }
  } catch (error) {
    console.error('Error loading reports:', error);
  }
}

// Placeholder functions
function editPosting(jobId) {
  // Redirect to edit page or open modal
  window.location.href = `postings.html?edit=${jobId}`;
}

async function sendNotification() {
  const message = prompt('Enter notification message:');
  if (!message) return;

  try {
    const res = await fetch(`${API_BASE}/api/officer/notifications`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({ message })
    });
    if (res.ok) {
      alert('Notification sent successfully!');
      loadOfficerNotifications(); // Refresh notifications
    } else {
      alert('Failed to send notification.');
    }
  } catch (error) {
    console.error('Error sending notification:', error);
    alert('Error sending notification.');
  }
}

// Search student by university roll number
async function searchStudentByRollNumber() {
  const rollNumber = document.getElementById('student-roll-search').value.trim();
  if (!rollNumber) {
    alert('Please enter a university roll number');
    return;
  }

  try {
    const res = await fetch(`${API_BASE}/api/officer/student/${rollNumber}`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    if (res.ok) {
      const student = await res.json();
      const resultDiv = document.getElementById('student-profile-result');
      resultDiv.style.display = 'block';
      resultDiv.innerHTML = `
        <h3>Student Profile</h3>
        <p><strong>Student ID:</strong> ${student.student_id}</p>
        <p><strong>University Roll Number:</strong> ${student.university_roll}</p>
        <p><strong>Name:</strong> ${student.name}</p>
        <p><strong>Email:</strong> ${student.email}</p>
        <p><strong>Branch:</strong> ${student.branch}</p>
        <p><strong>CGPA:</strong> ${student.cgpa}</p>
        <p><strong>Skills:</strong> ${student.skills.join(', ')}</p>
        <p><strong>Resume:</strong> ${student.resume_uploaded ? 'Uploaded' : 'Not uploaded'}</p>
      `;
    } else {
      const resultDiv = document.getElementById('student-profile-result');
      resultDiv.style.display = 'block';
      resultDiv.innerHTML = '<p>Student not found or invalid roll number.</p>';
    }
  } catch (error) {
    console.error('Error searching student:', error);
    alert('Failed to search student');
  }
}

// Load Officer Notifications
async function loadOfficerNotifications() {
  try {
    const res = await fetch(`${API_BASE}/api/officer/notifications`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    if (res.ok) {
      const notifications = await res.json();
      const notificationsList = document.getElementById('officer-notifications-list');
      if (notifications.length > 0) {
        notificationsList.innerHTML = notifications.map(notification => `
          <div class="notification-item">
            <p>${notification.message}</p>
            <span class="notification-time">${new Date(notification.created_at).toLocaleString()}</span>
          </div>
        `).join('');
      } else {
        notificationsList.innerHTML = '<div class="notification-item"><p>No notifications sent yet.</p></div>';
      }
    } else {
      document.getElementById('officer-notifications-list').innerHTML = '<div class="notification-item"><p>Failed to load notifications.</p></div>';
    }
  } catch (error) {
    console.error('Error loading notifications:', error);
    document.getElementById('officer-notifications-list').innerHTML = '<div class="notification-item"><p>Error loading notifications.</p></div>';
  }
}

// Load Application Pipeline
async function loadApplicationPipeline() {
  try {
    const postingsRes = await fetch(`${API_BASE}/api/officer/postings`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    const appsRes = await fetch(`${API_BASE}/api/officer/applications`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });

    if (postingsRes.ok && appsRes.ok) {
      const postings = await postingsRes.json();
      const applications = await appsRes.json();

      const pipelineContainer = document.getElementById('application-pipeline');

      if (postings.length === 0) {
        pipelineContainer.innerHTML = '<p>No job postings available.</p>';
        return;
      }

      // Group applications by job_id
      const appsByJob = {};
      applications.forEach(app => {
        if (!appsByJob[app.job_id]) {
          appsByJob[app.job_id] = [];
        }
        appsByJob[app.job_id].push(app);
      });

      // Create pipeline HTML
      const pipelineHTML = postings.map(posting => {
        const jobApps = appsByJob[posting.job_id] || [];
        const statuses = ['Applied', 'Shortlisted', 'Rejected'];

        const statusColumns = statuses.map(status => {
          const statusApps = jobApps.filter(app => app.status === status);
          const appCards = statusApps.map(app => `
            <div class="application-card">
              <input type="checkbox" class="application-checkbox" value="${app.application_id}" onchange="handleCheckboxChange(this)">
              <p><strong>${app.student_name}</strong></p>
              <p>Applied: ${new Date(app.applied_on).toLocaleDateString()}</p>
              <div class="application-actions">
                ${status !== 'Shortlisted' ? `<button class="btn-shortlist" onclick="updateApplicationStatus(${app.application_id}, 'Shortlisted')">Shortlist</button>` : ''}
                ${status !== 'Rejected' ? `<button class="btn-reject" onclick="updateApplicationStatus(${app.application_id}, 'Rejected')">Reject</button>` : ''}
              </div>
            </div>
          `).join('');

          return `
            <div class="pipeline-status-column">
              <h4>
                <input type="checkbox" onchange="toggleSelectAll('${posting.job_id}', '${status}', this.checked)">
                ${status} (${statusApps.length})
              </h4>
              <div class="pipeline-applications">
                ${appCards || '<p>No applications</p>'}
              </div>
            </div>
          `;
        }).join('');

        return `
          <div class="pipeline-job-column">
            <h3>${posting.title}</h3>
            ${statusColumns}
          </div>
        `;
      }).join('');

      pipelineContainer.innerHTML = pipelineHTML;
    } else {
      document.getElementById('application-pipeline').innerHTML = '<p>Failed to load pipeline.</p>';
    }
  } catch (error) {
    console.error('Error loading pipeline:', error);
    document.getElementById('application-pipeline').innerHTML = '<p>Error loading pipeline.</p>';
  }
}

// Update Application Status
async function updateApplicationStatus(applicationId, status) {
  try {
    const res = await fetch(`${API_BASE}/api/officer/applications/${applicationId}/status`, {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ status })
    });
    const result = await res.json();
    if (res.ok) {
      loadApplicationPipeline(); // Refresh pipeline
      loadOfficerReports(); // Update reports
    } else {
      alert(result.error || 'Failed to update application status');
    }
  } catch (error) {
    console.error('Error updating application status:', error);
    alert('Failed to update application status');
  }
}

// Handle individual checkbox change
function handleCheckboxChange(checkbox) {
  const statusColumn = checkbox.closest('.pipeline-status-column');
  const checkboxes = statusColumn.querySelectorAll('.application-checkbox');
  const selectAllCheckbox = statusColumn.querySelector('input[type="checkbox"][onchange*="toggleSelectAll"]');

  // Update select all checkbox state
  const checkedBoxes = Array.from(checkboxes).filter(cb => cb.checked);
  selectAllCheckbox.checked = checkedBoxes.length === checkboxes.length && checkboxes.length > 0;

  if (checkedBoxes.length > 0) {
    // Show bulk actions
    showBulkActions(statusColumn, checkedBoxes.map(cb => parseInt(cb.value)), statusColumn.querySelector('h4').textContent.split(' ')[0]);
  } else {
    // Hide bulk actions
    hideBulkActions(statusColumn);
  }
}

// Toggle Select All for a status column
function toggleSelectAll(jobId, status, checked) {
  const statusColumn = event.target.closest('.pipeline-status-column');
  const checkboxes = statusColumn.querySelectorAll('.application-checkbox');

  checkboxes.forEach(cb => {
    cb.checked = checked;
  });

  if (checked) {
    // Collect all selected application IDs
    const selectedIds = Array.from(checkboxes).filter(cb => cb.checked).map(cb => parseInt(cb.value));
    if (selectedIds.length > 0) {
      // Show bulk action buttons
      showBulkActions(statusColumn, selectedIds, status);
    }
  } else {
    // Hide bulk actions
    hideBulkActions(statusColumn);
  }
}

// Show bulk action buttons
function showBulkActions(statusColumn, selectedIds, currentStatus) {
  let bulkActions = statusColumn.querySelector('.bulk-actions');
  if (!bulkActions) {
    bulkActions = document.createElement('div');
    bulkActions.className = 'bulk-actions';
    bulkActions.style.marginTop = '10px';
    statusColumn.appendChild(bulkActions);
  }

  bulkActions.innerHTML = `
    <button class="btn-shortlist" onclick="bulkUpdateStatus(${JSON.stringify(selectedIds).replace(/"/g, "'")}, 'Shortlisted')" ${currentStatus === 'Shortlisted' ? 'disabled' : ''}>Bulk Shortlist</button>
    <button class="btn-reject" onclick="bulkUpdateStatus(${JSON.stringify(selectedIds).replace(/"/g, "'")}, 'Rejected')" ${currentStatus === 'Rejected' ? 'disabled' : ''}>Bulk Reject</button>
  `;
}

// Hide bulk actions
function hideBulkActions(statusColumn) {
  const bulkActions = statusColumn.querySelector('.bulk-actions');
  if (bulkActions) {
    bulkActions.remove();
  }
}

// Bulk update status
async function bulkUpdateStatus(applicationIds, status) {
  try {
    const res = await fetch(`${API_BASE}/api/officer/applications/bulk-status`, {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ application_ids: applicationIds, status })
    });
    const result = await res.json();
    if (res.ok) {
      alert(result.message);
      loadApplicationPipeline(); // Refresh pipeline
      loadOfficerReports(); // Update reports
    } else {
      alert(result.error || 'Failed to bulk update applications');
    }
  } catch (error) {
    console.error('Error bulk updating applications:', error);
    alert('Failed to bulk update applications');
  }
}

// Logout function
function logout() {
  localStorage.removeItem('token');
  localStorage.removeItem('role');
  window.location.href = '/';
}
