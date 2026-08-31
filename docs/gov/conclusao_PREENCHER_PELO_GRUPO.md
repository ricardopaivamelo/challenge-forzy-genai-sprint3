# Considerações Finais

Com a definição dos thresholds, quando aparece um alerta, conseguimos abri-lo e verificar qual valor ultrapassou o limite e qual era o limite esperado. Assim, é possível confiar ou desconfiar do alerta com base em algo concreto. Nos testes, houve um caso em que o sensor de temperatura apresentou erro enquanto a vibração estava crítica, e o sistema preferiu segurar o alerta em vez de confirmar uma falha com dados incompletos.

O grupo considera que a decisão de parar o motor nunca deve ser tomada somente pela máquina, pois ela afeta a segurança e toda a produção da planta. O alerta deve apoiar a avaliação, mas a responsabilidade pela parada continua sendo humana.

O protótipo ainda não pode ser usado diretamente em uma fábrica porque todos os dados são simulados. A aceleração também não vem de um sensor real, pois é calculada com base na vibração. Por isso, os limites precisariam ser recalibrados antes de qualquer uso industrial. A experiência do engenheiro continua necessária porque o sistema não consegue saber, por exemplo, que o motor recebeu manutenção no dia anterior ou que existe uma obra próxima causando vibrações. Esse contexto muda completamente a forma como a leitura deve ser interpretada.

No começo, a governança era apenas um conjunto de regras escritas. Depois, essas regras passaram a aparecer na tela e, agora, são executadas de verdade, fazendo com que o próprio sistema interrompa sua decisão quando não existe base suficiente para decidir.
