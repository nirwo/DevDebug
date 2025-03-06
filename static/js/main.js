document.addEventListener("DOMContentLoaded", function () {
  // Dashboard state
  let currentSection = 'dashboard';
  let activeTab = 'url-tab';
  let chartInstances = {};
  let errorData = {
    errors: [],
    currentPage: 1,
    itemsPerPage: 10,
    totalPages: 1
  };

  // DOM References
  const sidebarItems = document.querySelectorAll('.sidebar-nav li');
  const contentSections = document.querySelectorAll('.content-section');
  const tabButtons = document.querySelectorAll('.tab-btn');
  const tabPanes = document.querySelectorAll('.tab-pane');
  const notificationsToggle = document.getElementById('notifications-toggle');
  const notificationsPanel = document.querySelector('.notifications-panel');
  const newAnalysisBtn = document.getElementById('new-analysis-btn');
  const refreshDashboardBtn = document.getElementById('refresh-dashboard');
  const modalCloseBtn = document.querySelector('.modal-close');
  const errorDetailModal = document.getElementById('error-detail-modal');
  const modalTabs = document.querySelectorAll('.modal-tab');
  const modalTabContents = document.querySelectorAll('.modal-tab-content');
  const fileDropzone = document.getElementById('file-dropzone');
  const logFileInput = document.getElementById('log-file');
  const filePreview = document.getElementById('file-preview');
  const runAnalysisBtn = document.getElementById('run-analysis-btn');
  const analysisLoading = document.getElementById('analysis-loading');

  // Initialize the dashboard
  function initDashboard() {
    loadErrorData();
    initCharts();
    setupEventListeners();
  }

  // Load mock error data
  function loadErrorData() {
    // In a real application, this would be an API call
    errorData.errors = [
      {
        id: 'ERR-1001',
        timestamp: '2025-03-06 08:32:15',
        type: 'DatabaseError',
        message: 'Connection timeout: failed to connect to database after 30s',
        severity: 'critical',
        status: 'new'
      },
      {
        id: 'ERR-1002',
        timestamp: '2025-03-06 09:14:22',
        type: 'MemoryError',
        message: 'Out of memory: Killed process 12345 (node)',
        severity: 'error',
        status: 'investigating'
      },
      {
        id: 'ERR-1003',
        timestamp: '2025-03-06 10:05:51',
        type: 'NetworkError',
        message: 'Unable to connect to external API: Connection refused',
        severity: 'warning',
        status: 'resolved'
      },
      {
        id: 'ERR-1004',
        timestamp: '2025-03-05 14:32:10',
        type: 'SyntaxError',
        message: 'Unexpected token in JSON at position 43',
        severity: 'error',
        status: 'new'
      },
      {
        id: 'ERR-1005',
        timestamp: '2025-03-05 16:45:33',
        type: 'AuthenticationError',
        message: 'Invalid credentials: token expired',
        severity: 'critical',
        status: 'investigating'
      },
      {
        id: 'ERR-1006',
        timestamp: '2025-03-04 11:23:05',
        type: 'ValidationError',
        message: 'Required field "user_id" is missing',
        severity: 'warning',
        status: 'resolved'
      },
      {
        id: 'ERR-1007',
        timestamp: '2025-03-04 09:17:40',
        type: 'ConfigurationError',
        message: 'Invalid environment variable: REDIS_URL not defined',
        severity: 'error',
        status: 'resolved'
      },
      {
        id: 'ERR-1008',
        timestamp: '2025-03-03 17:56:12',
        type: 'PermissionError',
        message: 'Access denied: user lacks required permission "admin:write"',
        severity: 'critical',
        status: 'new'
      }
    ];

    updateDashboardKPIs();
    updateErrorsTable();
    errorData.totalPages = Math.ceil(errorData.errors.length / errorData.itemsPerPage);
    updatePagination();
  }

  // Set up event listeners
  function setupEventListeners() {
    // Sidebar navigation
    sidebarItems.forEach(item => {
      item.addEventListener('click', function() {
        const targetSection = this.getAttribute('data-section');
        switchSection(targetSection);
      });
    });

    // Tab navigation
    tabButtons.forEach(tab => {
      tab.addEventListener('click', function() {
        const targetTab = this.getAttribute('data-tab');
        switchTab(targetTab);
      });
    });

    // Notifications toggle
    if (notificationsToggle) {
      notificationsToggle.addEventListener('click', function(e) {
        e.stopPropagation();
        notificationsPanel.classList.toggle('active');
      });
    }

    // Close notifications panel when clicking outside
    document.addEventListener('click', function(e) {
      if (notificationsPanel && notificationsPanel.classList.contains('active') && 
          !notificationsPanel.contains(e.target) && 
          e.target !== notificationsToggle) {
        notificationsPanel.classList.remove('active');
      }
    });

    // New analysis button
    if (newAnalysisBtn) {
      newAnalysisBtn.addEventListener('click', function() {
        switchSection('analyze');
      });
    }

    // Refresh dashboard button
    if (refreshDashboardBtn) {
      refreshDashboardBtn.addEventListener('click', function() {
        // Show loading spinner or effect
        this.innerHTML = '<i class="fas fa-sync-alt fa-spin"></i> Refreshing...';
        this.disabled = true;
        
        // Simulate data refresh with a timeout
        setTimeout(() => {
          loadErrorData();
          refreshCharts();
          
          // Restore button
          this.innerHTML = '<i class="fas fa-sync-alt"></i> Refresh';
          this.disabled = false;
        }, 1000);
      });
    }

    // Modal close button
    if (modalCloseBtn) {
      modalCloseBtn.addEventListener('click', function() {
        errorDetailModal.classList.remove('active');
      });
    }

    // View details buttons in table
    document.addEventListener('click', function(e) {
      if (e.target.closest('.btn-icon') && e.target.closest('.actions-cell')) {
        openErrorDetailModal(e.target.closest('tr').cells[0].textContent);
      }
    });

    // View details buttons in error cards
    document.addEventListener('click', function(e) {
      if (e.target.closest('.btn.secondary.btn-sm') && e.target.closest('.error-card')) {
        const errorId = e.target.closest('.error-card').querySelector('.error-id').textContent;
        openErrorDetailModal(errorId);
      }
    });

    // Modal tabs
    modalTabs.forEach(tab => {
      tab.addEventListener('click', function() {
        const tabId = this.getAttribute('data-tab');
        modalTabs.forEach(t => t.classList.remove('active'));
        modalTabContents.forEach(c => c.classList.remove('active'));
        this.classList.add('active');
        document.getElementById(tabId).classList.add('active');
      });
    });

    // File dropzone
    if (fileDropzone) {
      fileDropzone.addEventListener('dragover', function(e) {
        e.preventDefault();
        this.classList.add('active');
      });

      fileDropzone.addEventListener('dragleave', function() {
        this.classList.remove('active');
      });

      fileDropzone.addEventListener('drop', function(e) {
        e.preventDefault();
        this.classList.remove('active');
        
        if (e.dataTransfer.files.length) {
          handleFileUpload(e.dataTransfer.files[0]);
        }
      });
    }

    // File input change
    if (logFileInput) {
      logFileInput.addEventListener('change', function() {
        if (this.files.length) {
          handleFileUpload(this.files[0]);
        }
      });
    }

    // Run analysis button
    if (runAnalysisBtn) {
      runAnalysisBtn.addEventListener('click', function(e) {
        e.preventDefault();
        simulateAnalysis();
      });
    }

    // Filter and search functionality
    const searchInput = document.getElementById('error-search');
    if (searchInput) {
      searchInput.addEventListener('input', function() {
        filterErrors();
      });
    }

    const severityFilter = document.getElementById('error-filter-severity');
    const statusFilter = document.getElementById('error-filter-status');
    if (severityFilter && statusFilter) {
      severityFilter.addEventListener('change', filterErrors);
      statusFilter.addEventListener('change', filterErrors);
    }

    // Table sorting
    const sortableHeaders = document.querySelectorAll('th.sortable');
    sortableHeaders.forEach(header => {
      header.addEventListener('click', function() {
        const sortField = this.getAttribute('data-sort');
        sortErrors(sortField);
      });
    });

    // Pagination
    const prevPageBtn = document.getElementById('prev-page');
    const nextPageBtn = document.getElementById('next-page');
    if (prevPageBtn && nextPageBtn) {
      prevPageBtn.addEventListener('click', function() {
        if (errorData.currentPage > 1) {
          errorData.currentPage--;
          updateErrorsTable();
          updatePagination();
        }
      });

      nextPageBtn.addEventListener('click', function() {
        if (errorData.currentPage < errorData.totalPages) {
          errorData.currentPage++;
          updateErrorsTable();
          updatePagination();
        }
      });
    }
  }

  // Switch between dashboard sections
  function switchSection(section) {
    sidebarItems.forEach(item => {
      item.classList.remove('active');
      if (item.getAttribute('data-section') === section) {
        item.classList.add('active');
      }
    });

    contentSections.forEach(content => {
      content.classList.remove('active');
      if (content.id === section) {
        content.classList.add('active');
      }
    });

    currentSection = section;

    // Refresh charts when switching to dashboard
    if (section === 'dashboard') {
      refreshCharts();
    }
  }

  // Switch between tabs
  function switchTab(tabId) {
    tabButtons.forEach(btn => {
      btn.classList.remove('active');
      if (btn.getAttribute('data-tab') === tabId) {
        btn.classList.add('active');
      }
    });

    tabPanes.forEach(pane => {
      pane.classList.remove('active');
      if (pane.id === tabId) {
        pane.classList.add('active');
      }
    });

    activeTab = tabId;
  }

  // Handle file upload for analysis
  function handleFileUpload(file) {
    // Show file preview
    if (filePreview) {
      filePreview.classList.add('active');
      filePreview.innerHTML = `
        <div class="file-info">
          <i class="fas fa-file-alt"></i>
          <div class="file-details">
            <p class="file-name">${file.name}</p>
            <p class="file-size">${formatFileSize(file.size)}</p>
          </div>
          <button class="btn-icon remove-file" title="Remove file">
            <i class="fas fa-times"></i>
          </button>
        </div>
      `;

      // Add remove button functionality
      const removeBtn = filePreview.querySelector('.remove-file');
      if (removeBtn) {
        removeBtn.addEventListener('click', function() {
          filePreview.classList.remove('active');
          filePreview.innerHTML = '';
          if (logFileInput) {
            logFileInput.value = '';
          }
        });
      }
    }
  }

  // Format file size in human-readable format
  function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }

  // Simulate log analysis
  function simulateAnalysis() {
    if (analysisLoading) {
      analysisLoading.style.display = 'flex';
      
      // Update progress and status message
      let progress = 0;
      const progressFill = analysisLoading.querySelector('.progress-fill');
      const statusMessage = document.getElementById('analysis-status-message');
      
      const progressInterval = setInterval(() => {
        progress += 10;
        if (progressFill) {
          progressFill.style.width = `${progress}%`;
        }
        
        // Update status messages based on progress
        if (statusMessage) {
          if (progress < 30) {
            statusMessage.textContent = 'Detecting error patterns...';
          } else if (progress < 60) {
            statusMessage.textContent = 'Analyzing root causes...';
          } else if (progress < 90) {
            statusMessage.textContent = 'Finding potential solutions...';
          } else {
            statusMessage.textContent = 'Finalizing analysis...';
          }
        }
        
        if (progress >= 100) {
          clearInterval(progressInterval);
          
          // Simulate new error being added
          const newError = {
            id: `ERR-${1000 + errorData.errors.length + 1}`,
            timestamp: new Date().toISOString().replace('T', ' ').substr(0, 19),
            type: 'SecurityError',
            message: 'Potential SQL injection detected in user input',
            severity: 'critical',
            status: 'new'
          };
          
          errorData.errors.unshift(newError);
          
          // Hide loading and show success
          setTimeout(() => {
            analysisLoading.style.display = 'none';
            
            // Show success notification
            alert('Analysis complete! A new critical error has been detected and added to the dashboard.');
            
            // Switch to dashboard
            switchSection('dashboard');
            
            // Update dashboard
            updateDashboardKPIs();
            updateErrorsTable();
            refreshCharts();
          }, 500);
        }
      }, 300);
    }
  }

  // Update dashboard KPI cards
  function updateDashboardKPIs() {
    const totalErrors = errorData.errors.length;
    const criticalErrors = errorData.errors.filter(e => e.severity === 'critical').length;
    const warningErrors = errorData.errors.filter(e => e.severity === 'warning').length;
    const resolvedErrors = errorData.errors.filter(e => e.status === 'resolved').length;
    
    document.getElementById('total-errors-kpi').textContent = totalErrors;
    document.getElementById('critical-errors-kpi').textContent = criticalErrors;
    document.getElementById('warning-errors-kpi').textContent = warningErrors;
    document.getElementById('resolved-errors-kpi').textContent = resolvedErrors;
    document.getElementById('error-count').textContent = totalErrors;
    document.getElementById('showing-count').textContent = `1-${Math.min(errorData.itemsPerPage, totalErrors)}`;
    document.getElementById('total-count').textContent = totalErrors;
  }

  // Update the errors table
  function updateErrorsTable() {
    const tableBody = document.getElementById('errors-table-body');
    if (!tableBody) return;
    
    // Clear existing rows
    tableBody.innerHTML = '';
    
    // Calculate pagination
    const startIndex = (errorData.currentPage - 1) * errorData.itemsPerPage;
    const endIndex = Math.min(startIndex + errorData.itemsPerPage, errorData.errors.length);
    
    // Get current page data
    const currentPageData = errorData.errors.slice(startIndex, endIndex);
    
    // Create and append rows
    currentPageData.forEach(error => {
      const row = document.createElement('tr');
      row.innerHTML = `
        <td>${error.id}</td>
        <td>${error.timestamp}</td>
        <td>${error.type}</td>
        <td class="error-message-cell">${error.message}</td>
        <td><span class="status-badge ${error.severity}">${capitalizeFirstLetter(error.severity)}</span></td>
        <td><span class="status-badge status-${error.status}">${capitalizeFirstLetter(error.status)}</span></td>
        <td class="actions-cell">
          <button class="btn-icon" title="View Details">
            <i class="fas fa-eye"></i>
          </button>
          <button class="btn-icon" title="Assign">
            <i class="fas fa-user-plus"></i>
          </button>
          <button class="btn-icon" title="More">
            <i class="fas fa-ellipsis-v"></i>
          </button>
        </td>
      `;
      tableBody.appendChild(row);
    });
  }

  // Update pagination controls
  function updatePagination() {
    const prevPageBtn = document.getElementById('prev-page');
    const nextPageBtn = document.getElementById('next-page');
    const pageInfo = document.getElementById('page-info');
    
    if (prevPageBtn && nextPageBtn && pageInfo) {
      prevPageBtn.disabled = errorData.currentPage === 1;
      nextPageBtn.disabled = errorData.currentPage === errorData.totalPages;
      pageInfo.textContent = `Page ${errorData.currentPage} of ${errorData.totalPages}`;
    }
  }

  // Filter errors based on search and filter criteria
  function filterErrors() {
    const searchTerm = document.getElementById('error-search')?.value.toLowerCase() || '';
    const severityFilter = document.getElementById('error-filter-severity')?.value || 'all';
    const statusFilter = document.getElementById('error-filter-status')?.value || 'all';
    
    // Get all data
    const allErrors = errorData.errors;
    
    // Apply filters
    const filteredErrors = allErrors.filter(error => {
      // Search term filter
      const matchesSearch = 
        error.id.toLowerCase().includes(searchTerm) ||
        error.type.toLowerCase().includes(searchTerm) ||
        error.message.toLowerCase().includes(searchTerm);
      
      // Severity filter
      const matchesSeverity = severityFilter === 'all' || error.severity === severityFilter;
      
      // Status filter
      const matchesStatus = statusFilter === 'all' || error.status === statusFilter;
      
      return matchesSearch && matchesSeverity && matchesStatus;
    });
    
    // Update the table with filtered data
    errorData.filteredErrors = filteredErrors;
    errorData.currentPage = 1;
    errorData.totalPages = Math.ceil(filteredErrors.length / errorData.itemsPerPage);
    
    // Temporarily replace errors array with filtered results
    const originalErrors = errorData.errors;
    errorData.errors = filteredErrors;
    
    updateErrorsTable();
    updatePagination();
    
    // Restore original array
    errorData.errors = originalErrors;
  }

  // Sort errors by field
  function sortErrors(field) {
    let sortDirection = 1; // 1 for ascending, -1 for descending
    
    // Toggle sort direction if sorting by the same field again
    const currentSortField = errorData.sortField;
    if (currentSortField === field) {
      sortDirection = errorData.sortDirection * -1;
    }
    
    // Store current sort criteria
    errorData.sortField = field;
    errorData.sortDirection = sortDirection;
    
    // Sort the errors array
    errorData.errors.sort((a, b) => {
      let valueA = a[field];
      let valueB = b[field];
      
      // Special handling for dates
      if (field === 'timestamp') {
        valueA = new Date(valueA).getTime();
        valueB = new Date(valueB).getTime();
      }
      
      if (valueA < valueB) return -1 * sortDirection;
      if (valueA > valueB) return 1 * sortDirection;
      return 0;
    });
    
    // Update the table
    updateErrorsTable();
    
    // Update sort indicators in the table header
    const headers = document.querySelectorAll('th.sortable');
    headers.forEach(header => {
      const headerField = header.getAttribute('data-sort');
      const icon = header.querySelector('i');
      
      if (headerField === field) {
        if (sortDirection === 1) {
          icon.className = 'fas fa-sort-up';
        } else {
          icon.className = 'fas fa-sort-down';
        }
      } else {
        icon.className = 'fas fa-sort';
      }
    });
  }

  // Open error detail modal
  function openErrorDetailModal(errorId) {
    // Find the error by ID
    const error = errorData.errors.find(e => e.id === errorId);
    if (!error) return;
    
    // Populate modal with error details
    document.getElementById('modal-error-id').textContent = error.id;
    document.getElementById('modal-error-time').textContent = error.timestamp;
    document.getElementById('modal-error-type').textContent = error.type;
    
    // Set severity badge
    const severityElement = document.getElementById('modal-error-severity');
    severityElement.innerHTML = `<span class="status-badge ${error.severity}">${capitalizeFirstLetter(error.severity)}</span>`;
    
    // Set status badge
    const statusElement = document.getElementById('modal-error-status');
    statusElement.innerHTML = `<span class="status-badge status-${error.status}">${capitalizeFirstLetter(error.status)}</span>`;
    
    // Set technology (based on error type)
    let technology = 'Unknown';
    if (error.type.includes('Database')) {
      technology = 'PostgreSQL';
    } else if (error.type.includes('Memory')) {
      technology = 'Node.js';
    } else if (error.type.includes('Network')) {
      technology = 'API Service';
    } else if (error.type.includes('Syntax')) {
      technology = 'JavaScript';
    } else if (error.type.includes('Authentication')) {
      technology = 'Auth Service';
    }
    document.getElementById('modal-error-tech').textContent = technology;
    
    // Set error message
    document.getElementById('modal-error-message').textContent = error.message;
    
    // Generate mock context based on error type
    let context = '';
    switch (error.type) {
      case 'DatabaseError':
        context = `2025-03-06 08:32:10.123 INFO  [pool-2-thread-1] Attempting to connect to database at db-prod-01.example.com:5432
2025-03-06 08:32:15.234 WARN  [pool-2-thread-1] Database connection attempt 1 failed: timeout
2025-03-06 08:32:20.345 WARN  [pool-2-thread-1] Database connection attempt 2 failed: timeout
2025-03-06 08:32:25.456 WARN  [pool-2-thread-1] Database connection attempt 3 failed: timeout
2025-03-06 08:32:30.567 ERROR [pool-2-thread-1] Connection timeout: failed to connect to database after 30s
2025-03-06 08:32:30.678 ERROR [pool-2-thread-1] Application startup failed
2025-03-06 08:32:30.789 ERROR [main] java.sql.SQLException: Connection timed out
    at com.example.db.ConnectionManager.getConnection(ConnectionManager.java:142)
    at com.example.service.DatabaseService.initialize(DatabaseService.java:58)
    at com.example.Application.start(Application.java:87)
    at com.example.Application.main(Application.java:31)`;
        break;
      case 'MemoryError':
        context = `2025-03-06 09:14:15.452 INFO  [app] Server running with 4GB allocated memory
2025-03-06 09:14:18.734 INFO  [app] Processing large data batch
2025-03-06 09:14:20.128 WARN  [app] Memory usage at 85% (3.4GB/4GB)
2025-03-06 09:14:21.562 WARN  [app] Memory usage at 95% (3.8GB/4GB)
2025-03-06 09:14:22.103 ERROR [app] Out of memory: Killed process 12345 (node)
2025-03-06 09:14:22.234 ERROR [system] Process terminated with signal: SIGKILL
2025-03-06 09:14:22.456 ERROR [system] Core dump written to /var/crash/core.12345`;
        break;
      default:
        context = `${error.timestamp.split(' ')[0]} ${error.timestamp.split(' ')[1].split(':')[0]}:${error.timestamp.split(' ')[1].split(':')[1]}:00.123 INFO  [app] Operation started
${error.timestamp} ERROR [app] ${error.message}
${error.timestamp.split(' ')[0]} ${error.timestamp.split(' ')[1].split(':')[0]}:${parseInt(error.timestamp.split(' ')[1].split(':')[1])+1}:00.456 ERROR [app] Operation failed with status code 500`;
    }
    document.getElementById('modal-error-context').textContent = context;
    
    // Activate first tab
    document.querySelector('.modal-tab[data-tab="error-details-tab"]').click();
    
    // Show modal
    errorDetailModal.classList.add('active');
    
    // Initialize error timeline chart if on metrics tab
    initErrorTimelineChart();
  }

  // Initialize charts
  function initCharts() {
    initErrorDistributionChart();
    initErrorTrendsChart();
  }

  // Refresh all charts
  function refreshCharts() {
    if (chartInstances.errorDistribution) {
      chartInstances.errorDistribution.updateSeries([
        errorData.errors.filter(e => e.severity === 'critical').length,
        errorData.errors.filter(e => e.severity === 'error').length,
        errorData.errors.filter(e => e.severity === 'warning').length
      ]);
    } else {
      initErrorDistributionChart();
    }
    
    if (chartInstances.errorTrends) {
      // Update with new data
      const dates = getLast7Days();
      const criticalData = dates.map(date => 
        errorData.errors.filter(e => 
          e.severity === 'critical' && e.timestamp.startsWith(date)
        ).length
      );
      const errorData2 = dates.map(date => 
        errorData.errors.filter(e => 
          e.severity === 'error' && e.timestamp.startsWith(date)
        ).length
      );
      const warningData = dates.map(date => 
        errorData.errors.filter(e => 
          e.severity === 'warning' && e.timestamp.startsWith(date)
        ).length
      );
      
      chartInstances.errorTrends.updateSeries([
        { name: 'Critical', data: criticalData },
        { name: 'Error', data: errorData2 },
        { name: 'Warning', data: warningData }
      ]);
    } else {
      initErrorTrendsChart();
    }
  }

  // Initialize error distribution chart
  function initErrorDistributionChart() {
    const chartElement = document.getElementById('error-distribution-chart');
    if (!chartElement) return;
    
    const options = {
      series: [
        errorData.errors.filter(e => e.severity === 'critical').length,
        errorData.errors.filter(e => e.severity === 'error').length,
        errorData.errors.filter(e => e.severity === 'warning').length
      ],
      chart: {
        type: 'donut',
        height: 280
      },
      colors: ['#dc3545', '#fd7e14', '#ffc107'],
      labels: ['Critical', 'Error', 'Warning'],
      legend: {
        position: 'bottom'
      },
      dataLabels: {
        enabled: false
      },
      plotOptions: {
        pie: {
          donut: {
            size: '60%',
            labels: {
              show: true,
              total: {
                show: true,
                label: 'Total',
                formatter: function (w) {
                  return w.globals.seriesTotals.reduce((a, b) => a + b, 0);
                }
              }
            }
          }
        }
      }
    };
    
    chartInstances.errorDistribution = new ApexCharts(chartElement, options);
    chartInstances.errorDistribution.render();
  }

  // Initialize error trends chart
  function initErrorTrendsChart() {
    const chartElement = document.getElementById('error-trends-chart');
    if (!chartElement) return;
    
    // Get dates for the last 7 days
    const dates = getLast7Days();
    
    // Count errors for each day
    const criticalData = dates.map(date => 
      errorData.errors.filter(e => 
        e.severity === 'critical' && e.timestamp.startsWith(date)
      ).length
    );
    const errorData2 = dates.map(date => 
      errorData.errors.filter(e => 
        e.severity === 'error' && e.timestamp.startsWith(date)
      ).length
    );
    const warningData = dates.map(date => 
      errorData.errors.filter(e => 
        e.severity === 'warning' && e.timestamp.startsWith(date)
      ).length
    );
    
    const options = {
      series: [
        { name: 'Critical', data: criticalData },
        { name: 'Error', data: errorData2 },
        { name: 'Warning', data: warningData }
      ],
      chart: {
        type: 'area',
        height: 280,
        stacked: false,
        toolbar: {
          show: false
        }
      },
      colors: ['#dc3545', '#fd7e14', '#ffc107'],
      dataLabels: {
        enabled: false
      },
      stroke: {
        curve: 'smooth',
        width: 2
      },
      fill: {
        type: 'gradient',
        gradient: {
          opacityFrom: 0.6,
          opacityTo: 0.1
        }
      },
      legend: {
        position: 'top',
        horizontalAlign: 'right'
      },
      xaxis: {
        categories: dates,
        labels: {
          rotate: 0,
          style: {
            fontSize: '11px'
          }
        }
      },
      yaxis: {
        min: 0,
        forceNiceScale: true,
        labels: {
          formatter: function(val) {
            return val.toFixed(0);
          }
        }
      },
      tooltip: {
        shared: true,
        intersect: false
      }
    };
    
    chartInstances.errorTrends = new ApexCharts(chartElement, options);
    chartInstances.errorTrends.render();
    
    // Add period button functionality
    const periodButtons = document.querySelectorAll('.period-btn');
    periodButtons.forEach(button => {
      button.addEventListener('click', function() {
        periodButtons.forEach(btn => btn.classList.remove('active'));
        this.classList.add('active');
        
        const period = this.getAttribute('data-period');
        updateTrendsChartPeriod(period);
      });
    });
  }

  // Initialize error timeline chart in the modal
  function initErrorTimelineChart() {
    const chartElement = document.getElementById('modal-error-timeline-chart');
    if (!chartElement) return;
    
    // Generate mock data for the error occurrence timeline
    const today = new Date();
    const dates = [];
    const counts = [];
    
    for (let i = 10; i >= 0; i--) {
      const date = new Date(today);
      date.setDate(date.getDate() - i);
      dates.push(formatDate(date));
      
      // Random count between 0 and 5
      counts.push(Math.floor(Math.random() * 6));
    }
    
    const options = {
      series: [{
        name: 'Occurrences',
        data: counts
      }],
      chart: {
        height: 250,
        type: 'bar',
        toolbar: {
          show: false
        }
      },
      colors: ['#4a6cf7'],
      plotOptions: {
        bar: {
          borderRadius: 4,
          columnWidth: '60%'
        }
      },
      dataLabels: {
        enabled: false
      },
      xaxis: {
        categories: dates,
        axisBorder: {
          show: false
        },
        labels: {
          style: {
            fontSize: '10px'
          }
        }
      },
      yaxis: {
        min: 0,
        max: 5,
        tickAmount: 5,
        labels: {
          formatter: function(val) {
            return val.toFixed(0);
          }
        }
      },
      toolbar: {
        tools: {
          download: false
        }
      }
    };
    
    // If chart already exists, destroy it
    if (chartInstances.errorTimeline) {
      chartInstances.errorTimeline.destroy();
    }
    
    chartInstances.errorTimeline = new ApexCharts(chartElement, options);
    chartInstances.errorTimeline.render();
  }

  // Update error trends chart based on selected period
  function updateTrendsChartPeriod(period) {
    if (!chartInstances.errorTrends) return;
    
    let dates;
    let criticalData, errorData2, warningData;
    
    switch (period) {
      case 'week':
        dates = getLast7Days();
        break;
      case 'month':
        dates = getLast30Days();
        break;
      case 'year':
        dates = getLast12Months();
        break;
      default:
        dates = getLast7Days();
    }
    
    // Count errors for the selected period
    criticalData = dates.map(date => 
      errorData.errors.filter(e => 
        e.severity === 'critical' && e.timestamp.startsWith(date)
      ).length
    );
    errorData2 = dates.map(date => 
      errorData.errors.filter(e => 
        e.severity === 'error' && e.timestamp.startsWith(date)
      ).length
    );
    warningData = dates.map(date => 
      errorData.errors.filter(e => 
        e.severity === 'warning' && e.timestamp.startsWith(date)
      ).length
    );
    
    chartInstances.errorTrends.updateOptions({
      xaxis: {
        categories: dates
      }
    });
    
    chartInstances.errorTrends.updateSeries([
      { name: 'Critical', data: criticalData },
      { name: 'Error', data: errorData2 },
      { name: 'Warning', data: warningData }
    ]);
  }

  // Helper function to get array of last 7 days in YYYY-MM-DD format
  function getLast7Days() {
    const result = [];
    for (let i = 6; i >= 0; i--) {
      const date = new Date();
      date.setDate(date.getDate() - i);
      result.push(formatDate(date));
    }
    return result;
  }

  // Helper function to get array of last 30 days in YYYY-MM-DD format
  function getLast30Days() {
    const result = [];
    for (let i = 29; i >= 0; i--) {
      const date = new Date();
      date.setDate(date.getDate() - i);
      result.push(formatDate(date));
    }
    return result;
  }

  // Helper function to get array of last 12 months in YYYY-MM format
  function getLast12Months() {
    const result = [];
    for (let i = 11; i >= 0; i--) {
      const date = new Date();
      date.setMonth(date.getMonth() - i);
      result.push(formatMonth(date));
    }
    return result;
  }

  // Format date as YYYY-MM-DD
  function formatDate(date) {
    const year = date.getFullYear();
    const month = (date.getMonth() + 1).toString().padStart(2, '0');
    const day = date.getDate().toString().padStart(2, '0');
    return `${year}-${month}-${day}`;
  }

  // Format date as YYYY-MM
  function formatMonth(date) {
    const year = date.getFullYear();
    const month = (date.getMonth() + 1).toString().padStart(2, '0');
    return `${year}-${month}`;
  }

  // Capitalize first letter of a string
  function capitalizeFirstLetter(string) {
    return string.charAt(0).toUpperCase() + string.slice(1);
  }

  // Initialize the dashboard on page load
  initDashboard();
});