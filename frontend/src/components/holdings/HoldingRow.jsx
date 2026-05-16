function HoldingRow({ holding }) {
	return (
		<tr>
			<td>{holding.ticker}</td>
			<td>{holding.quantity}</td>
		</tr>
	)
}

export default HoldingRow
