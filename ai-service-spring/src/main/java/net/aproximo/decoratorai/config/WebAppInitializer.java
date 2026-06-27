package net.aproximo.decoratorai.config;

import jakarta.servlet.ServletContext;
import jakarta.servlet.ServletException;
import org.springframework.context.annotation.Configuration;
import org.springframework.core.env.Environment;
import org.springframework.web.WebApplicationInitializer;

@Configuration
public class WebAppInitializer
        implements WebApplicationInitializer {

    private Environment env;

    @Override
    public void onStartup(ServletContext servletContext) throws ServletException {

        String mode = env.getProperty("spring.application.mode");
        if (mode != null && mode.equals("production")){
                servletContext.setInitParameter(
                        "spring.profiles.active", "production");
                return;
        }
        servletContext.setInitParameter(
                "spring.profiles.active", "development"
        );

    }
}