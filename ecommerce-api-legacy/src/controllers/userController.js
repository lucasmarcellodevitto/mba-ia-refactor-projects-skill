class UserController {
    constructor(userRepository) {
        this.userRepository = userRepository;
    }

    remove = async (req, res) => {
        try {
            await this.userRepository.deleteById(req.params.id);
        } catch (err) {
            // Comportamento original preservado: falha na exclusão não é verificada,
            // a resposta de sucesso abaixo é sempre enviada.
        }
        res.send("Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco.");
    };
}

module.exports = UserController;
