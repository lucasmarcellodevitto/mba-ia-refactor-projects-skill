class FinancialReportService {
    constructor(financialReportRepository) {
        this.financialReportRepository = financialReportRepository;
    }

    async buildReport() {
        const rows = await this.financialReportRepository.findReportRows();

        const courseMap = new Map();

        for (const row of rows) {
            if (!courseMap.has(row.course_id)) {
                courseMap.set(row.course_id, {
                    course: row.course_title,
                    revenue: 0,
                    students: [],
                });
            }

            if (row.enrollment_id === null) continue;

            const courseData = courseMap.get(row.course_id);

            if (row.payment_status === 'PAID') {
                courseData.revenue += row.payment_amount;
            }

            courseData.students.push({
                student: row.student_name || 'Unknown',
                paid: row.payment_amount || 0,
            });
        }

        return Array.from(courseMap.values());
    }
}

module.exports = FinancialReportService;
