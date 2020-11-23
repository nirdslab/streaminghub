interface WSResponse<T> {
  command: string,
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