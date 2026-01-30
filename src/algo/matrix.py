class Matrix:
    """
    Класс для работы с матрицами.
    """

    def __init__(self, rows: int, cols: int):
        """
        Инициализация матрицы.

        Args:
            rows (int): количество строк.
            cols (int): количество столбцов.
        """
        self.rows = rows
        self.cols = cols
        self.data = [[0 for _ in range(cols)] for _ in range(rows)]

    def multiply(self, other_matrix: 'Matrix') -> 'Matrix':
        """
        Умножение матрицы на другую матрицу.

        Args:
            other_matrix (Matrix): матрица для умножения.

        Returns:
            Matrix: результат умножения матриц.

        Raises:
            ValueError: если количество столбцов первой матрицы не равно количеству строк второй матрицы.
        """
        if self.cols != other_matrix.rows:
            raise ValueError("Количество столбцов первой матрицы должно быть равно количеству строк второй матрицы.")

        result = Matrix(self.rows, other_matrix.cols)
        for i in range(self.rows):
            for j in range(other_matrix.cols):
                for k in range(self.cols):
                    result.data[i][j] += self.data[i][k] * other_matrix.data[k][j]
        return result

    def transpose(self) -> 'Matrix':
        """
        Транспонирование матрицы.

        Returns:
            Matrix: транспонированная матрица.
        """
        transposed = Matrix(self.cols, self.rows)
        for i in range(self.rows):
            for j in range(self.cols):
                transposed.data[j][i] = self.data[i][j]
        return transposed
