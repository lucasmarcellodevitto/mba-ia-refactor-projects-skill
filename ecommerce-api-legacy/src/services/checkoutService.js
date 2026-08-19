const { hashPassword } = require('../utils/passwordHasher');

const DEFAULT_PASSWORD = "123456";
const VISA_CARD_PREFIX = "4";

class CheckoutError extends Error {
    constructor(status, message) {
        super(message);
        this.status = status;
    }
}

class CheckoutService {
    constructor({ userRepository, courseRepository, enrollmentRepository, paymentRepository, auditLogRepository, cache }) {
        this.userRepository = userRepository;
        this.courseRepository = courseRepository;
        this.enrollmentRepository = enrollmentRepository;
        this.paymentRepository = paymentRepository;
        this.auditLogRepository = auditLogRepository;
        this.cache = cache;
    }

    async checkout({ username, email, password, courseId, cardNumber }) {
        if (!username || !email || !courseId || !cardNumber) {
            throw new CheckoutError(400, "Bad Request");
        }

        let course;
        try {
            course = await this.courseRepository.findActiveById(courseId);
        } catch (err) {
            throw new CheckoutError(500, "Erro DB");
        }
        if (!course) {
            throw new CheckoutError(404, "Curso não encontrado");
        }

        let existingUser;
        try {
            existingUser = await this.userRepository.findIdByEmail(email);
        } catch (err) {
            throw new CheckoutError(500, "Erro DB");
        }

        let userId;
        if (!existingUser) {
            try {
                const passwordHash = hashPassword(password || DEFAULT_PASSWORD);
                const created = await this.userRepository.create({ name: username, email, passwordHash });
                userId = created.lastID;
            } catch (err) {
                throw new CheckoutError(500, "Erro ao criar usuário");
            }
        } else {
            userId = existingUser.id;
        }

        const paymentStatus = cardNumber.startsWith(VISA_CARD_PREFIX) ? "PAID" : "DENIED";
        if (paymentStatus === "DENIED") {
            throw new CheckoutError(400, "Pagamento recusado");
        }

        let enrollment;
        try {
            enrollment = await this.enrollmentRepository.create(userId, courseId);
        } catch (err) {
            throw new CheckoutError(500, "Erro Matrícula");
        }

        try {
            await this.paymentRepository.create(enrollment.lastID, course.price, paymentStatus);
        } catch (err) {
            throw new CheckoutError(500, "Erro Pagamento");
        }

        try {
            await this.auditLogRepository.create(`Checkout curso ${courseId} por ${userId}`);
        } catch (err) {
            // Auditoria é best-effort: comportamento original ignorava falha aqui e mantinha o checkout como sucesso.
        }

        this.cache.set(`last_checkout_${userId}`, course.title);

        return { enrollmentId: enrollment.lastID };
    }
}

module.exports = { CheckoutService, CheckoutError };
