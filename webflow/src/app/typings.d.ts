interface WSResponse<T> {
  error: {
    code: number
    message: string
  },
  data: T
}

interface WSRequest<T> {
  command: string,
  data?: T
}