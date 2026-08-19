const { CheckoutError } = require('../services/checkoutService');

class CheckoutController {
    constructor(checkoutService) {
        this.checkoutService = checkoutService;
    }

    checkout = async (req, res) => {
        try {
            const result = await this.checkoutService.checkout({
                username: req.body.usr,
                email: req.body.eml,
                password: req.body.pwd,
                courseId: req.body.c_id,
                cardNumber: req.body.card,
            });

            res.status(200).json({ msg: "Sucesso", enrollment_id: result.enrollmentId });
        } catch (err) {
            if (err instanceof CheckoutError) {
                return res.status(err.status).send(err.message);
            }
            res.status(500).send("Erro DB");
        }
    };
}

module.exports = CheckoutController;
