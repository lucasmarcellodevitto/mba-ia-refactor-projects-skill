class AdminController {
    constructor(financialReportService) {
        this.financialReportService = financialReportService;
    }

    financialReport = async (req, res) => {
        try {
            const report = await this.financialReportService.buildReport();
            res.json(report);
        } catch (err) {
            res.status(500).send("Erro DB");
        }
    };
}

module.exports = AdminController;
