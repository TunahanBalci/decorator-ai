package net.aproximo.decoratorai.config;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.jdbc.DataSourceBuilder;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Profile;
import org.springframework.core.env.Environment;

import javax.sql.DataSource;
import java.util.Objects;
import java.util.Properties;

@Configuration
@Profile("production")
public class DataSourceConfig {

    @Autowired
    private Environment env;

    @Bean
    @Profile("production")
    public DataSource getDataSource() {

        DataSourceBuilder dataSourceBuilder = DataSourceBuilder.create();
        dataSourceBuilder.driverClassName(Objects.requireNonNull(
                env.getProperty("spring.datasource.driver-class-name")));
             dataSourceBuilder.url(Objects.requireNonNull(
                env.getProperty("spring.datasource.url")));
         dataSourceBuilder.username(env.getProperty("spring.datasource.user"));
        dataSourceBuilder.password(env.getProperty("spring.datasource.password"));
         return dataSourceBuilder.build();
    }
}
