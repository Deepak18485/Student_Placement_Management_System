// Officer Dashboard specific JavaScript

document.addEventListener('DOMContentLoaded', () => {
  loadOfficerProfile();
  loadActivePostings();
  loadRecentApplications();
  loadOfficerReports();
});

// Load Officer Profile Info
async function loadOfficerProfile() {
  try {
    // Assume there's a profile endpoint for officer
    const res = await fetch(`${API_BASE}/officer/profile`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    if (res.ok) {
      const profile = await res.json();
      const profileInfo = document.getElementById('officer-profile-info');
      profileInfo.innerHTML = `
        <p><strong>Name:</strong> ${profile.name}</p>
        <p><strong>Email:</strong> ${profile.email}</p>
        <p><strong>Department:</strong> ${profile.department || 'N/A'}</p>
        <p><strong>Contact:</strong> ${profile.contact || 'N/A'}</p>
      `;
    } else {
      document.getElementById('officer-profile-info').innerHTML = '<p>Profile not available.</p>';
    }
  } catch (error) {
    console.error('Error loading officer profile:', error);
    document.getElementById('officer-profile-info').innerHTML = '<p>Error loading profile.</p>';
  }
}

// Load Active Postings
async function loadActivePostings() {
  try {
    const res = await fetch(`${API_BASE}/officer/postings`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    if (res.ok) {
      const postings = await res.json();
      const activePostings = document.getElementById('active-postings');
      if (postings.length > 0) {
        activePostings.innerHTML = postings.slice(0, 3).map(posting => `
          <div class="posting-card">
            <h3>${posting.title}</h3>
            <p><strong>Company:</strong> ${posting.company || 'N/A'}</p>
            <p><strong>Deadline:</strong> ${new Date(posting.deadline).toLocaleDateString()}</p>
            <p><strong>Applications:</strong> ${posting.application_count || 0}</p>
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

// Load Recent Applications
async function loadRecentApplications() {
  try {
    // Assume fetch all applications for officer
    const res = await fetch(`${API_BASE}/officer/applications`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    if (res.ok) {
      const apps = await res.json();
      const recentApps = document.getElementById('recent-applications');
      if (apps.length > 0) {
        recentApps.innerHTML = `
          <table>
            <thead>
              <tr>
                <th>Student Name</th>
                <th>Job Title</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              ${apps.slice(0, 5).map(app => `
                <tr>
                  <td>${app.student_name}</td>
                  <td>${app.job_title}</td>
                  <td>${app.status}</td>
                  <td>
                    <button onclick="updateStatus(${app.application_id}, 'Shortlisted')">Shortlist</button>
                    <button onclick="updateStatus(${app.application_id}, 'Selected')">Select</button>
                    <button onclick="updateStatus(${app.application_id}, 'Rejected')">Reject</button>
                  </td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        `;
      } else {
        recentApps.innerHTML = '<p>No recent applications.</p>';
      }
    } else {
      document.getElementById('recent-applications').innerHTML = '<p>Failed to load applications.</p>';
    }
  } catch (error) {
    console.error('Error loading applications:', error);
    document.getElementById('recent-applications').innerHTML = '<p>Error loading applications.</p>';
  }
}

// Load Officer Reports
async function loadOfficerReports() {
  try {
    // Fetch postings and applications to calculate reports
    const postingsRes = await fetch(`${API_BASE}/officer/postings`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    const appsRes = await fetch(`${API_BASE}/officer/applications`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    if (postingsRes.ok && appsRes.ok) {
      const postings = await postingsRes.json();
      const apps = await appsRes.json();
      const totalPostings = postings.length;
      const totalApps = apps.length;
      const selected = apps.filter(app => app.status === 'Selected').length;
      const packages = apps.filter(app => app.status === 'Selected' && app.package).map(app => parseFloat(app.package));
      const avgPackage = packages.length > 0 ? (packages.reduce((a, b) => a + b, 0) / packages.length).toFixed(2) : 0;

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

function sendNotification() {
  // Placeholder for sending notification
  alert('Notification feature not implemented yet.');
}
