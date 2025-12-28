# No trecho onde é renderizado o card de treino, substitua por:

if not selected_workout.empty:
    workout = selected_workout.iloc[0]
    zone_color = zone_colors.get(workout["Zona FC"], "#4361ee")
    
    # Card de treino estilizado
    st.markdown(f"""
    <div class="workout-card">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
            <h3 style="margin: 0; color: #4361ee;">Treino do dia {workout['Dia']}</h3>
            <div style="background: {zone_color}20; color: {zone_color}; padding: 0.3rem 0.8rem; border-radius: 20px; font-size: 0.9rem; font-weight: 500;">
                {workout['Dia da Semana']}
            </div>
        </div>
        
        <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 1rem; margin-bottom: 1.5rem;">
            <div style="background: #f8f9fa; padding: 1rem; border-radius: 8px; transition: all 0.3s ease;">
                <p style="margin: 0 0 0.3rem; font-size: 0.9rem; color: #6c757d;">Tipo de Treino</p>
                <p style="margin: 0; font-weight: 500;">{workout['Tipo de Treino']}</p>
            </div>
            
            <div style="background: #f8f9fa; padding: 1rem; border-radius: 8px; transition: all 0.3s ease;">
                <p style="margin: 0 0 0.3rem; font-size: 0.9rem; color: #6c757d;">Duração</p>
                <p style="margin: 0; font-weight: 500;">{workout['Duração']}</p>
            </div>
            
            <div style="background: #f8f9fa; padding: 1rem; border-radius: 8px; transition: all 0.3s ease;">
                <p style="margin: 0 0 0.3rem; font-size: 0.9rem; color: #6c757d;">Zona FC</p>
                <p style="margin: 0; font-weight: 500; color: {zone_color};">{workout['Zona FC']}</p>
            </div>
            
            <div style="background: #f8f9fa; padding: 1rem; border-radius: 8px; transition: all 0.3s ease;">
                <p style="margin: 0 0 0.3rem; font-size: 0.9rem; color: #6c757d;">Intensidade</p>
                <p style="margin: 0; font-weight: 500;">{workout['Intensidade']}</p>
            </div>
        </div>
        
        <div style="background: #f8f9fa; padding: 1rem; border-radius: 8px; margin-bottom: 1rem; transition: all 0.3s ease;">
            <p style="margin: 0 0 0.5rem; font-weight: 500; color: #6c757d;">Descrição do Treino</p>
            <p style="margin: 0;">{workout['Descrição']}</p>
        </div>
        
        <div style="display: flex; gap: 1rem;">
            <button style="background: #4361ee; color: white; border: none; padding: 0.5rem 1rem; border-radius: 8px; cursor: pointer; transition: all 0.3s ease; font-weight: 500;">✅ Marcar como Concluído</button>
            <button style="background: white; color: #4361ee; border: 1px solid #4361ee; padding: 0.5rem 1rem; border-radius: 8px; cursor: pointer; transition: all 0.3s ease; font-weight: 500;">✏️ Editar Treino</button>
        </div>
    </div>
    """, unsafe_allow_html=True)
else:
    st.warning("Nenhum treino encontrado para a data selecionada.")
