// Edição da proposta na tela de revisão: a mudança vale na hora na tela e os envios saem em fila, cada um com a
// proposta já com todas as mudanças feitas até ali (cliques rápidos não desfazem uns aos outros).

export class EdicaoProposta<T extends object> {
  private local: T
  private fila: Promise<unknown> = Promise.resolve()

  constructor(
    inicial: T,
    private readonly enviar: (proposta: T) => Promise<unknown>,
    private readonly aoFalhar: (e: unknown) => void = () => {},
  ) {
    this.local = structuredClone(inicial)
  }

  get proposta(): T {
    return this.local
  }

  /** Resolve quando todos os envios em fila terminaram (antes de confirmar a importação). */
  esperar(): Promise<void> {
    return this.fila.then(() => undefined)
  }

  alterar(mudar: (p: T) => void): Promise<void> {
    const copia = structuredClone(this.local)
    mudar(copia)
    this.local = copia
    const envio = this.fila.then(async () => {
      try {
        await this.enviar(structuredClone(this.local))
      } catch (e) {
        this.aoFalhar(e)
      }
    })
    this.fila = envio
    return envio
  }
}
