const express = require('express');

const Database = require('./db/database');
const { initSchema } = require('./db/schema');

const UserRepository = require('./repositories/userRepository');
const CourseRepository = require('./repositories/courseRepository');
const EnrollmentRepository = require('./repositories/enrollmentRepository');
const PaymentRepository = require('./repositories/paymentRepository');
const AuditLogRepository = require('./repositories/auditLogRepository');
const FinancialReportRepository = require('./repositories/financialReportRepository');

const { CheckoutService } = require('./services/checkoutService');
const FinancialReportService = require('./services/financialReportService');

const CheckoutController = require('./controllers/checkoutController');
const AdminController = require('./controllers/adminController');
const UserController = require('./controllers/userController');

const createRouter = require('./routes');
const Cache = require('./utils/cache');

const PORT = 3000;

const database = new Database(':memory:');
initSchema(database);

const userRepository = new UserRepository(database);
const courseRepository = new CourseRepository(database);
const enrollmentRepository = new EnrollmentRepository(database);
const paymentRepository = new PaymentRepository(database);
const auditLogRepository = new AuditLogRepository(database);
const financialReportRepository = new FinancialReportRepository(database);

const cache = new Cache();

const checkoutService = new CheckoutService({
    userRepository,
    courseRepository,
    enrollmentRepository,
    paymentRepository,
    auditLogRepository,
    cache,
});
const financialReportService = new FinancialReportService(financialReportRepository);

const checkoutController = new CheckoutController(checkoutService);
const adminController = new AdminController(financialReportService);
const userController = new UserController(userRepository);

const app = express();
app.use(express.json());
app.use(createRouter({ checkoutController, adminController, userController }));

app.listen(PORT, () => {
    console.log(`Frankenstein LMS rodando na porta ${PORT}...`);
});
