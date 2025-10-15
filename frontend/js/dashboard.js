// Dashboard specific JavaScript

document.addEventListener('DOMContentLoaded', () => {
  loadProfile();
  loadOpportunities();
  loadApplications();
  loadReports();
});

// Load Profile Info
async function loadProfile() {
  try {
    const res = await fetch(`${API_BASE}/student/profile`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    if (res.ok) {
      const profile = await res.json();
      const profileInfo = document.getElementById('profile-info');
      profileInfo.innerHTML = `
        <p><strong>Name:</strong> ${profile.name}</p>
        <p><strong>Email:</strong> ${profile.email}</p>
        <p><strong>Branch:</strong> ${profile.branch}</p>
        <p><strong>CGPA:</strong> ${profile.cgpa}</p>
        <p><strong>Skills:</strong> ${profile.skills.join(', ')}</p>
        <p><strong>Resume:</strong> ${profile.resume ? 'Uploaded' : 'Not uploaded'}</p>
      `;
    } else {
      document.getElementById('profile-info').innerHTML = '<p>Failed to load profile.</p>';
    }
  } catch (error) {
    console.error('Error loading profile:', error);
    document.getElementById('profile-info').innerHTML = '<p>Error loading profile.</p>';
  }
}

// Load Available Opportunities
async function loadOpportunities() {
  try {
    const res = await fetch(`${API_BASE}/student/jobs`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    if (res.ok) {
      const jobs = await res.json();
      const opportunitiesList = document.getElementById('opportunities-list');
      if (jobs.length > 0) {
        opportunitiesList.innerHTML = jobs.slice(0, 3).map(job => `
          <div class="opportunity-card">
            <h3>${job.title}</h3>
            <p><strong>Company:</strong> ${job.company || 'N/A'}</p>
            <p><strong>Eligibility:</strong> Branch: ${job.branch_eligibility}, CGPA: ${job.min_cgpa}</p>
            <p><strong>Package:</strong> ${job.package_stipend}</p>
            <p><strong>Deadline:</strong> ${new Date(job.deadline).toLocaleDateString()}</p>
            <button onclick="apply(${job.job_id})">Apply</button>
          </div>
        `).join('');
      } else {
        opportunitiesList.innerHTML = '<p>No opportunities available.</p>';
      }
    } else {
      document.getElementById('opportunities-list').innerHTML = '<p>Failed to load opportunities.</p>';
    }
  } catch (error) {
    console.error('Error loading opportunities:', error);
    document.getElementById('opportunities-list').innerHTML = '<p>Error loading opportunities.</p>';
  }
}

// Load Application Tracking
async function loadApplications() {
  try {
    const res = await fetch(`${API_BASE}/student/applications`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    if (res.ok) {
      const apps = await res.json();
      const applicationsTable = document.getElementById('applications-table');
      if (apps.length > 0) {
        applicationsTable.innerHTML = `
          <table>
            <thead>
              <tr>
                <th>Job Title</th>
                <th>Status</th>
                <th>Applied Date</th>
              </tr>
            </thead>
            <tbody>
              ${apps.slice(0, 5).map(app => `
                <tr>
                  <td>${app.title}</td>
                  <td>${app.status}</td>
                  <td>${new Date(app.applied_at).toLocaleDateString()}</td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        `;
      } else {
        applicationsTable.innerHTML = '<p>No applications yet.</p>';
      }
    } else {
      document.getElementById('applications-table').innerHTML = '<p>Failed to load applications.</p>';
    }
  } catch (error) {
    console.error('Error loading applications:', error);
    document.getElementById('applications-table').innerHTML = '<p>Error loading applications.</p>';
  }
}

// Load Reports
async function loadReports() {
  try {
    const res = await fetch(`${API_BASE}/student/applications`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    if (res.ok) {
      const apps = await res.json();
      const total = apps.length;
      const shortlisted = apps.filter(app => app.status === 'Shortlisted').length;
      const selected = apps.filter(app => app.status === 'Selected').length;
      const rejected = apps.filter(app => app.status === 'Rejected').length;

      document.getElementById('total-applications').textContent = total;
      document.getElementById('shortlisted-count').textContent = shortlisted;
      document.getElementById('selected-count').textContent = selected;
      document.getElementById('rejected-count').textContent = rejected;
    }
  } catch (error) {
    console.error('Error loading reports:', error);
  }
}
