const express = require('express');

function createRouter({ checkoutController, adminController, userController }) {
    const router = express.Router();

    router.post('/api/checkout', checkoutController.checkout);
    router.get('/api/admin/financial-report', adminController.financialReport);
    router.delete('/api/users/:id', userController.remove);

    return router;
}

module.exports = createRouter;
