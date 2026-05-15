/** Sample analytics data until wired to API */

export const weekLabels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

export const dashboardPresets = {
  admin: {
    stats: [
      { key: 'users', label: 'Total users', value: '1,284', hint: '+4.2% this week', tone: 'indigo', icon: 'users' },
      { key: 'students', label: 'Students', value: '892', hint: 'Active enrollments', tone: 'violet', icon: 'graduation' },
      { key: 'sessions', label: 'Sessions (7d)', value: '156', hint: 'Attendance', tone: 'emerald', icon: 'calendar' },
      { key: 'reports', label: 'Reports', value: '48', hint: 'Pending review: 3', tone: 'amber', icon: 'document' },
    ],
    trend: weekLabels.map((name, i) => ({
      name,
      value: 120 + i * 18 + (i % 3) * 12,
    })),
    bars: [
      { name: 'Math', value: 42 },
      { name: 'Science', value: 38 },
      { name: 'English', value: 35 },
      { name: 'Arts', value: 22 },
    ],
    activity: [
      { id: '1', title: 'New user registered', subtitle: 'teacher2@school.com', time: '12 min ago', tone: 'indigo' },
      { id: '2', title: 'Weekly report generated', subtitle: 'School scope — Week 14', time: '1 hr ago', tone: 'violet' },
      { id: '3', title: 'Attendance session completed', subtitle: 'Grade 5 — Math', time: '2 hrs ago', tone: 'emerald' },
      { id: '4', title: 'Low grade alert batch', subtitle: '12 notifications sent', time: '4 hrs ago', tone: 'amber' },
    ],
  },
  teacher: {
    stats: [
      { key: 'classes', label: 'My classes', value: '6', hint: 'This term', tone: 'indigo', icon: 'layers' },
      { key: 'students', label: 'Students taught', value: '142', hint: 'Across subjects', tone: 'violet', icon: 'users' },
      { key: 'sessions', label: 'Sessions (7d)', value: '11', hint: 'Face + manual', tone: 'emerald', icon: 'camera' },
      { key: 'avg', label: 'Avg. score', value: '78%', hint: 'Last assessments', tone: 'amber', icon: 'chart' },
    ],
    trend: weekLabels.map((name, i) => ({
      name,
      value: 40 + i * 6 + (i % 2) * 8,
    })),
    bars: [
      { name: 'Quiz', value: 18 },
      { name: 'Midterm', value: 12 },
      { name: 'Lab', value: 9 },
      { name: 'HW', value: 24 },
    ],
    activity: [
      { id: '1', title: 'Exam grades published', subtitle: 'Algebra — Section A', time: '25 min ago', tone: 'indigo' },
      { id: '2', title: 'Video uploaded', subtitle: 'Introduction to fractions', time: '3 hrs ago', tone: 'violet' },
      { id: '3', title: 'Session started', subtitle: 'Face attendance', time: 'Yesterday', tone: 'emerald' },
      { id: '4', title: 'Report filed', subtitle: 'Student S042', time: 'Yesterday', tone: 'amber' },
    ],
  },
  student: {
    stats: [
      { key: 'gpa', label: 'Avg. grade', value: '84%', hint: 'Last 30 days', tone: 'indigo', icon: 'chart' },
      { key: 'att', label: 'Attendance', value: '96%', hint: 'This month', tone: 'emerald', icon: 'check' },
      { key: 'due', label: 'Due soon', value: '2', hint: 'Assignments', tone: 'amber', icon: 'clock' },
      { key: 'videos', label: 'Videos watched', value: '14', hint: 'Library', tone: 'violet', icon: 'play' },
    ],
    trend: weekLabels.map((name, i) => ({
      name,
      value: 65 + i * 4 + (i % 2) * 5,
    })),
    bars: [
      { name: 'Math', value: 88 },
      { name: 'Science', value: 82 },
      { name: 'English', value: 79 },
      { name: 'PE', value: 92 },
    ],
    activity: [
      { id: '1', title: 'New grade posted', subtitle: 'Science quiz', time: '1 hr ago', tone: 'indigo' },
      { id: '2', title: 'Report available', subtitle: 'Mid-term progress', time: '5 hrs ago', tone: 'violet' },
      { id: '3', title: 'Attendance marked', subtitle: 'Present — Mon', time: '1 day ago', tone: 'emerald' },
      { id: '4', title: 'Video assigned', subtitle: 'Algebra recap', time: '2 days ago', tone: 'amber' },
    ],
  },
  parent: {
    stats: [
      { key: 'kids', label: 'Children', value: '2', hint: 'Linked accounts', tone: 'indigo', icon: 'heart' },
      { key: 'att', label: 'Avg. attendance', value: '94%', hint: 'Household', tone: 'emerald', icon: 'calendar' },
      { key: 'grades', label: 'Avg. grade', value: '81%', hint: 'Combined', tone: 'violet', icon: 'chart' },
      { key: 'alerts', label: 'Open alerts', value: '1', hint: 'Action optional', tone: 'amber', icon: 'bell' },
    ],
    trend: weekLabels.map((name, i) => ({
      name,
      value: 55 + i * 5 + (i % 3) * 3,
    })),
    bars: [
      { name: 'Child A', value: 85 },
      { name: 'Child B', value: 78 },
    ],
    activity: [
      { id: '1', title: 'Teacher message', subtitle: 'Field trip form', time: '30 min ago', tone: 'indigo' },
      { id: '2', title: 'Grade update', subtitle: 'Child A — Math', time: '6 hrs ago', tone: 'violet' },
      { id: '3', title: 'Attendance notice', subtitle: 'Child B — absent (excused)', time: '1 day ago', tone: 'emerald' },
      { id: '4', title: 'Report published', subtitle: 'Behavior — Week 12', time: '3 days ago', tone: 'amber' },
    ],
  },
}
